from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from io import BytesIO
import cv2
import numpy as np
import tensorflow as tf
import logging
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

with open('token.txt', 'r') as f:
    TOKEN = f.read().strip()

(x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()
x_train, x_test = x_train / 255.0, x_test / 255.0
    
class_names = ['Plane', 'Car', 'Bike', 'Truck', 'Bird', 'Cat', 'Dog', 'Deer', 'Hen', 'Frog', 'Ship', 'Horse']

model = tf.keras.models.Sequential([
    tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(32, 32, 3)),
    tf.keras.layers.MaxPooling2D(2, 2),
    tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
    tf.keras.layers.MaxPooling2D(2, 2),
    tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dense(12, activation='softmax') 
])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
        /start - Starts conversation
        /help - Shows this message
        /train - Trains neural network
    """)

async def train(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Model is being trained...")
    logging.info("Start model training...")
    
    try:
        model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        model.fit(x_train, y_train, epochs=2, validation_data=(x_test, y_test))
        model.save(os.path.join(base_dir, 'cifar_classifier.model'))
        logging.info("Model training completed and saved.")
        await update.message.reply_text("Done! You can now send a photo.")

    except Exception as e:
        logger.error(f"An error occurred during training: {e}")
        await update.message.reply_text(f"An error occurred during training: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Train the Model and send picture")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await context.bot.get_file(update.message.photo[-1].file_id)
    f = BytesIO(await file.download_as_bytearray())
    file_bytes = np.asarray(bytearray(f.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Ensure correct color conversion
    img = cv2.resize(img, (32, 32), interpolation=cv2.INTER_AREA)
    prediction = model.predict(np.array([img / 255.0]))
    class_index = np.argmax(prediction)
    class_name = class_names[class_index]
    await update.message.reply_text(f"I see a {class_name}")

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("train", train))

app.add_handler(MessageHandler(filters.Filters.text & ~filters.Filters.command, handle_message))
app.add_handler(MessageHandler(filters.Filters.photo, handle_photo))

app.run_polling()
