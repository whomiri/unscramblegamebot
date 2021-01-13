from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging, random, string, time
import threading 
import os

TOKEN= '1595433915:AAEvoy7AHWHGbB4G8ohxTr93QEuKkpJ-IIk'
bot_id = int(TOKEN.split(':')[0])

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

updater = Updater(token=TOKEN, use_context=True)
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
        if chat_id in games:
            if user["id"] not in games[chat_id]["players"] and not games[chat_id]["active"]:
                games[chat_id]["players"][user['id']] = {"score":0, "data":user}
                context.bot.send_message(chat_id=update.effective_chat.id, text="You've joined the game!")
                context.bot.send_message(chat_id=chat_id, text=f'[{user["first_name"]}](tg://user?id={user["id"]}) joined the game', parse_mode='markdown')
                return
            elif games[chat_id]["active"]:
                context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, you can't join an active game.")
                return
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="There's no game session for this group. Start one by sending the /startGame command in the group")
            return
        return
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi and welcome to the Unscramble Game Bot!\n\nA bot for playing unscramble competitively in groups. Add this bot to your group to start playing.")

def players(update, context):
    chat_id = update.message.chat_id
    if chat_id not in games:
        update.message.reply_text("Hal hazırda aktiv oyun yoxdur, oyun başlatmağ üçün /startgame yazın")
        return
    players = games[chat_id]["players"]
    finalPlayers = {k: v for k, v in sorted(players.items(), key=lambda item: item[1]['score'], reverse=True)}
    players = [(k, v) for k, v in finalPlayers.items()]
    message = 'Players:\n'
    for item in players:
        message += f'[{item[1]["data"]["first_name"]}](tg://user?id={item[1]["data"]["id"]})\n'
    update.message.reply_markdown(message)

def sendEndTimer(update, context, remaining, index):
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=f"{remaining} left to end of game")
    games[chat_id]["gameEndTimers"][index+1].start()

def gameEnder(update, context):
    chat_id = update.message.chat_id
    if chat_id not in games:
        update.message.reply_text("Hal hazırda aktiv oyun yoxdur, oyun başlatmağ üçün /startgame yazın")
        return
    timers = games[chat_id]["gameEndTimers"]
    for item in timers:
        if(hasattr(item, 'cancel')):
            item.cancel()
    games[chat_id]["active"] = False
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'The correct word is {games[chat_id]["correct"]}')
    games[chat_id]["timer"].cancel()
    players = games[chat_id]["players"]
    context.bot.send_message(chat_id=chat_id, text="Ending this game session, calculating scores...")
    finalPlayers = {k: v for k, v in sorted(players.items(), key=lambda item: item[1]['score'], reverse=True)}
    players = [(k, v) for k, v in finalPlayers.items()]
    winner = players[0]
    if(winner[1]["score"] == 0):
        message = "There's no winner\n\nplayers:\n"
    else:
        message = f'The Winner is [{winner[1]["data"]["first_name"]}](tg://user?id={winner[1]["data"]["id"]})\nscore: {winner[1]["score"]}\n\nPlayers:\n'
    for item in players:
        message += f'{item[1]["data"]["first_name"]}: {item[1]["score"]}\n'
    update.message.reply_markdown(message)
    del games[chat_id]

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
        games[chat_id]["timer"] = threading.Timer(25.0, wordTimeOut, args=(update,context))
        games[chat_id]["timer"].start()

def welcome_group_addition(update, context):
    new_members = update.message.new_chat_members
    for member in new_members:
        if(member.id==bot_id):
            context.bot.send_message(chat_id=update.effective_chat.id, text="Hi! You just added the Unscramble Game bot to your group. \n\nTo start a game, use the /startGame command and join the game using the join button.\n\nBy continuing to use this bot, you are agreeing to the /terms of service. Enjoy!")
            

def checkGroupAddition(update, context):
    if(len(update.message.new_chat_members)):
        return welcome_group_addition(update, context)

def checkSolution(update, context):
    chat_id = update.message.chat_id
    if chat_id in games and games[chat_id]["active"]:
        solution = update.message.text.strip().split()[0]
        user = update.message.from_user
        if(not games[chat_id]["solved"] and solution.lower()==games[chat_id]["correct"].lower()):
            games[chat_id]["solved"] = True
            games[chat_id]["timer"].cancel()
            update.message.reply_markdown(f'[{user["first_name"]} {user["last_name"]}](tg://user?id={user["id"]})  solved the word 🥳🥳')
            games[chat_id]["players"][user["id"]]["score"] += 1
            return setAndSendWord(update, context)

def extendJoinTime(update, context):
    chat_id = update.message.chat_id
    if chat_id not in games:
        update.message.reply_text("Hal hazırda aktiv oyun yoxdur, oyun başlatmağ üçün /startgame yazın")
        return
    timers = games[chat_id]["gameStarterTimers"]
    for item in timers:
        if(hasattr(item, 'cancel')):
            item.cancel()
    context.bot.send_message(chat_id=chat_id, text="Join time extended. You can always /force start the game.")
    games[chat_id]["gameStarterTimers"] = [
                threading.Timer(30, sendRemainingTime, args=(update,context, 'one minute', 0)),
                threading.Timer(30, sendRemainingTime, args=(update,context, '30 seconds', 1)),
                threading.Timer(20, sendRemainingTime, args=(update,context, '10 seconds',2)),
                threading.Timer(10, gameStarter, args=(update,context)),
            ]
    games[chat_id]["gameStarterTimers"][0].start()

def forceStartGame(update, context):
    chat_id = update.message.chat_id
    if chat_id not in games:
        update.message.reply_text("Hal hazırda aktiv oyun yoxdur, oyun başlatmağ üçün /startgame yazın")
        return
    players = games[chat_id]["players"]
    if(len(players) >=2 ):
        timers = games[chat_id]["gameStarterTimers"]
        for item in timers:
            if(hasattr(item, 'cancel')):
                item.cancel()
        context.bot.send_message(chat_id=update.effective_chat.id, text='Starting game... Buckle Up!')
        games[update.message.chat_id]["active"] = True
        games[update.message.chat_id]["gameEndTimers"] = [
                    threading.Timer(60, sendEndTimer, args=(update,context,'two minutes',0)),
                    threading.Timer(60, sendEndTimer, args=(update,context, 'one minute', 1)),
                    threading.Timer(30, sendEndTimer, args=(update,context, '30 seconds', 2)),
                    threading.Timer(20, sendEndTimer, args=(update,context, '10 seconds', 3)),
                    threading.Timer(10, gameEnder, args=(update,context)),
                ]
        games[update.message.chat_id]["gameEndTimers"][0].start()
        return setAndSendWord(update, context)
    else:
        update.message.reply_text('Oyuna başlamağ üçün ən azı 2 nəfərə ehtiyac vardır')
        
def gameStarter(update, context):
    chat_id = update.message.chat_id
    players = games[chat_id]["players"]
    if(len(players) >=2 ):
        games[update.message.chat_id]["active"] = True
        games[update.message.chat_id]["gameEndTimers"] = [
                    threading.Timer(60, sendEndTimer, args=(update,context,'two minutes',0)),
                    threading.Timer(60, sendEndTimer, args=(update,context, 'one minute', 1)),
                    threading.Timer(30, sendEndTimer, args=(update,context, '30 seconds', 2)),
                    threading.Timer(20, sendEndTimer, args=(update,context, '10 seconds', 3)),
                    threading.Timer(10, gameEnder, args=(update,context)),
                ]
        games[update.message.chat_id]["gameEndTimers"][0].start()
        context.bot.send_message(chat_id=update.effective_chat.id, text='Starting game... Buckle Up!')
        return setAndSendWord(update, context)
    else:
        context.bot.send_message(chat_id=chat_id, text='Not enough players. Cancelling game...')
        del games[chat_id]

def sendRemainingTime(update, context, remaining, index):
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=f'{remaining} left to join game')
    games[chat_id]["gameStarterTimers"][index+1].start()

def startGame(update, context):

    chat_id = update.message.chat_id

    if chat_id not in games:
        games[chat_id] = {
            "current": "", 
            "correct": "", 
            "solved": True, 
            "active": False, 
            "players": {},
            "gameStarterTimers": [
                threading.Timer(30, sendRemainingTime, args=(update,context, 'one minute', 0)),
                threading.Timer(30, sendRemainingTime, args=(update,context, '30 seconds', 1)),
                threading.Timer(20, sendRemainingTime, args=(update,context, '10 seconds', 2)),
                threading.Timer(10, gameStarter, args=(update,context)),
            ]
        }

        keyboard = [[InlineKeyboardButton("Join", url=f'https://t.me/unscramblegamebot?start={chat_id}', callback_data='1')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Giraffe oyunu başladıldı!\nQoşulmağ üçün düyməni klikləyin.\n\nYou can always /force start the game.', reply_markup=reply_markup)
        games[chat_id]["gameStarterTimers"][0].start()

def terms(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text='*Terms of Service:* \n\nI hereby agree to send @ahmedXabdeen a bag of homemade cookies whenever he asks for them.')

start_handler = CommandHandler('start', start)
terms_handler = CommandHandler('terms', terms)
end_handler = CommandHandler('end', gameEnder)
players_handler = CommandHandler('players', players)
startGame_handler = CommandHandler('startGame', startGame)
extendJoinTime_handler = CommandHandler('extend', extendJoinTime)
forceStartGame_handler = CommandHandler('force', forceStartGame)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(terms_handler)
dispatcher.add_handler(end_handler)
dispatcher.add_handler(players_handler)
dispatcher.add_handler(startGame_handler)
dispatcher.add_handler(extendJoinTime_handler)
dispatcher.add_handler(forceStartGame_handler)
dispatcher.add_handler(MessageHandler(Filters.text, checkSolution))
dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, checkGroupAddition), group=9)

updater.start_polling()
updater.idle()
