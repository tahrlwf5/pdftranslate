# bot.py
import os
import io
import logging
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from googletrans import Translator
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Initialize translator
translator = Translator()

# Configuration
TOKEN = os.environ.get('TELEGRAM_TOKEN')
PORT = int(os.environ.get('PORT', 8443))
WEBHOOK_URL = os.environ.get('RAILWAY_STATIC_URL')  # Get Railway public URL

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحبًا! أرسل لي ملف PDF باللغة الإنجليزية وسأقوم بترجمته إلى العربية.\n\n"
        "Hello! Send me an English PDF file and I'll translate it to Arabic."
    )

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Get the PDF file
        file = await update.message.document.get_file()
        file_bytes = await file.download_as_bytearray()
        
        # Convert to bytes stream
        pdf_stream = io.BytesIO(file_bytes)
        
        # Extract text from PDF
        extracted_text = []
        reader = PdfReader(pdf_stream)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text.append(text)
        
        # Translate text
        translated_text = []
        for text in extracted_text:
            translated = translator.translate(text, src='en', dest='ar').text
            translated_text.append(translated)
        
        # Create translated PDF
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=letter)
        c.setFont("Helvetica", 12)
        
        y = 700
        for text in translated_text:
            c.drawString(72, y, text)
            y -= 50
            if y < 50:
                c.showPage()
                y = 700
        c.save()
        
        packet.seek(0)
        
        # Send translated PDF back
        await update.message.reply_document(
            document=InputFile(packet, filename='translated.pdf'),
            caption="Here's your translated PDF!"
        )
        
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        await update.message.reply_text("Sorry, there was an error processing your PDF. Please try again.")

def main():
    # Create application
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    
    # Configure for Railway
    if WEBHOOK_URL:
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}/telegram",
            url_path=TOKEN
        )
    else:
        # Local polling
        application.run_polling()

if __name__ == '__main__':
    main()
