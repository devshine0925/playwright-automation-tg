from telegram.ext import Updater, MessageHandler, filters
def message_handler(update, context):
    message = update.message
    print(message.text)

# Create the Updater and pass it the bot's token
updater = Updater("TOKEN", use_context=True)

# Get the dispatcher to register handlers
dp = updater.dispatcher

# Add a message handler that will be called for any message
dp.add_handler(MessageHandler(filters.text, message_handler))

# Start the bot
updater.start_polling()

# Run the bot until you press Ctrl-C or the process receives SIGINT,
# SIGTERM or SIGABRT. This should be used most of the time, since
# start_polling() is non-blocking and will stop the bot gracefully.
updater.idle()