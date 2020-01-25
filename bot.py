from telegram.ext import Updater, CommandHandler, MessageHandler, BaseFilter, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging, random, string
import threading 

class FilterNoShit(BaseFilter):
    def filter(self, message):
        return True

this_filter_aint_filtering_shit = FilterNoShit()


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

updater = Updater(token='TOKEN', use_context=True)
dispatcher = updater.dispatcher

games = {}

words = []

with open("words.txt") as f:
    for w in f:
        words.append(w.strip())

def start(update, context):
    if(len(context.args)):
        user = update.message.from_user
        chat_id = int(context.args[0])
        games[chat_id]["players"][user['id']] = {"score":0, "data":user}
        context.bot.send_message(chat_id=update.effective_chat.id, text="You've joined the game!")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Hi and welcome to the Unscramble Game Bot!\n\nA bot for playing unscramble competitively in groups. Add this bot to your group to start playing.")

def gameEnder(update, context):
    chat_id = update.message.chat_id
    games[chat_id]["active"] = False
    games[chat_id]["timer"].cancel()
    players = games[chat_id]["players"]
    update.message.reply_text("Ending this game session, calculating scores...")
    finalPlayers = {k: v for k, v in sorted(players.items(), key=lambda item: item[1]['score'], reverse=True)}
    players = [(k, v) for k, v in finalPlayers.items()]
    winner = players[0]
    message = f"""The Winner is [{winner[1]["data"]["first_name"]} {winner[1]["data"]["last_name"]}](tg://user?id={winner[1]["data"]["id"]})\nscore: {winner[1]["score"]}\n\nPlayers:\n"""
    for item in players:
        message += f'{item[1]["data"]["first_name"]} {item[1]["data"]["last_name"]}: {item[1]["score"]}\n'
    update.message.reply_markdown(message)
    del games[chat_id]
    
    # stop generating words, calculate results & send them, and send achievemnts
    pass

def wordTimeOut(update, context):
    chat_id = update.message.chat_id
    games[chat_id]["solved"] = True
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'The correct word is {games[chat_id]["correct"]}')
    return setAndSendWord(update, context)

def setAndSendWord(update, context):
    chat_id = update.message.chat_id
    if games[chat_id]["solved"] and games[chat_id]["active"]:
        new_w = list(random.choice(words))
        games[chat_id]["correct"] = "".join(new_w)

        random.shuffle(new_w)
        games[chat_id]["current"] = "".join(new_w)
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"The word to solve is: \n{games[chat_id]['current']}")

        games[chat_id]["solved"] = False
        games[chat_id]["timer"] = threading.Timer(15.0, wordTimeOut, args=(update,context))
        games[chat_id]["timer"].start()

    

def welcome_group_addition(update, context):
    new_members = update.message.new_chat_members
    for member in new_members:
        if(member.id=='bot_id'):
            context.bot.send_message(chat_id=update.effective_chat.id, text="Hi! You just added the Unscramble Game bot to your group. \nTo start a game, use the /startGame command and join the game using the join button.\nBy continuing to use this bot, you are agreeing to the /terms of service. Enjoy!")
            

def checkGroupAddition(update, context):
    if(len(update.message.new_chat_members)):
        return welcome_group_addition(update, context)

def checkSolution(update, context):
    chat_id = update.message.chat_id
    if chat_id in games and games[chat_id]["active"]:
        solution = update.message.text.strip().split()[0]
        user = update.message.from_user
        if(not games[chat_id]["solved"] and solution==games[chat_id]["correct"]):
            games[chat_id]["solved"] = True
            games[chat_id]["timer"].cancel()
            update.message.reply_markdown(f'[{user["first_name"]} {user["last_name"]}](tg://user?id={user["id"]})  solved the word 🥳🥳')
            games[chat_id]["players"][user["id"]]["score"] += 1
            return setAndSendWord(update, context)

def startGame(update, context):

    chat_id = update.message.chat_id

    if chat_id not in games:
        games[chat_id] = {"current": "", "correct": "", "solved": True, "active": False, "players": {}}

        keyboard = [[InlineKeyboardButton("Join", url=f'https://t.me/unscramblegamebot?start={chat_id}', callback_data='1')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text('An unscamble game is starting!\nJoin the game using the join button. When you\'re ready, use the /startGame command again to start the game.', reply_markup=reply_markup)
    elif(len(games[chat_id]["players"]) >= 1):
        context.bot.send_message(chat_id=update.effective_chat.id, text='Starting game... Buckle Up!')
        games[chat_id]["active"] = True
        return setAndSendWord(update, context)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='You need at least two players to start the game.')


def terms(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text='*Terms of Service:* \n\nI hereby agree to send @ahmedXabdeen a box of homemade cookies whenever he asks for them.')







start_handler = CommandHandler('start', start)
terms_handler = CommandHandler('terms', terms)
end_handler = CommandHandler('end', gameEnder)
startGame_handler = CommandHandler('startGame', startGame)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(terms_handler)
dispatcher.add_handler(end_handler)
dispatcher.add_handler(startGame_handler)
dispatcher.add_handler(MessageHandler(Filters.text, checkSolution))
dispatcher.add_handler(MessageHandler(this_filter_aint_filtering_shit, checkGroupAddition), group=9)


updater.start_polling()

updater.idle()


