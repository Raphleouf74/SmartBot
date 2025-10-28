import os
import re
import json
import random
import asyncio
import subprocess
from datetime import timedelta, datetime

import discord
from discord.ext import commands, tasks
from discord.ui import View, Button, Select
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from threading import Thread

import wikipedia
from deep_translator import GoogleTranslator
import yt_dlp
import gdown
VOLUME = 1.0  # Volume par défaut (1.0 = 100%)
MUSIC_DIR = "Musics"
DRIVE_URL = "https://drive.google.com/drive/folders/12ykstPlTFiyGeTklVnNsfatJegFNtqRY"

os.makedirs(MUSIC_DIR, exist_ok=True)

# Télécharger les fichiers depuis le Drive
print("🔽 Téléchargement des musiques depuis Google Drive...")
try:
    gdown.download_folder(DRIVE_URL, output=MUSIC_DIR, quiet=False, use_cookies=False)
    print("✅ Téléchargement terminé.")
except Exception as e:
    print(f"❌ Impossible de télécharger depuis Google Drive : {e}")
    print("➡️ Les musiques seront prises depuis le dossier local /Musics/")

os.makedirs(MUSIC_DIR, exist_ok=True)

os.environ["PATH"] += os.pathsep + os.path.abspath("ffmpeg/bin")


import subprocess
print(subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout)



API_KEY = os.getenv("API_KEY", "2JX9F7bN1kL0aYQp")  # déjà mis
app = Flask(__name__)

def check_key():
    key = request.args.get("key")
    if key != API_KEY:
        abort(403)

@app.route("/status")
def status():
    check_key()
    return jsonify({
        "status": "online" if bot.is_ready() else "starting",
        "bot": str(bot.user) if bot.user else "starting...",
        "servers": len(bot.guilds),
        "users": sum(g.member_count for g in bot.guilds)
    })

@app.route("/servers")
def servers():
    check_key()
    return jsonify([
        {"id": str(g.id), "name": g.name, "members": g.member_count}
        for g in bot.guilds
    ])
    
@app.route("/commands")
def list_commands():
    check_key()
    return jsonify({
        "ping": "Affiche le ping du bot",
        "userinfo": "Montre les infos d’un utilisateur",
        "help": "Liste toutes les commandes"
    })

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") # ton token de bot
API_KEY = os.getenv("API_KEY")  # clé secrète API
OWNER_ID = 1067745915915481098


# Init bot Discord
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Init Flask
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://smartdcbot.netlify.app"]}})

@app.route("/")
def home():
    return "✅ SmartBot API est en ligne. Utilise /status pour vérifier l'état du bot."

@app.route("/status")
def status():
    key = request.args.get("key")
    if key != API_KEY:
        abort(403)  # accès refusé

    return jsonify({
        "status": "running",
        "bot": str(bot.user) if bot.user else "starting...",
        "servers": len(bot.guilds),
        "users": sum(g.member_count for g in bot.guilds)
    })

def run_flask():
    port = int(os.environ.get("PORT", 5000))  # Render fournit PORT automatiquement
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()


with open("questions.json", "r", encoding="utf-8") as f:
    questions_quiz = json.load(f)

# Charger et filtrer les mots
with open("mots.txt", "r", encoding="utf-8") as f:
    mots_pendu = []
    for mot in f:
        mot = mot.strip().lower()
        # Garder uniquement les mots :
        # - sans accents/caractères spéciaux
        # - de 4 à 12 lettres
        # - non interdits
        if re.match("^[a-z]{4,12}$", mot):
            mots_pendu.append(mot)

print(f"✅ {len(mots_pendu)} mots valides chargés pour le pendu")


# Charger les mots du fichier
with open("mots.txt", "r", encoding="utf-8") as f:
    mots_pendu = [mot.strip().lower() for mot in f if mot.strip()]




# -------------------------
# Configuration des intents
# -------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="+", intents=intents)
bot.remove_command("help")
warns = {}

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="📖 Menu d’aide",
        description="Voici la liste des commandes disponibles :",
        color=discord.Color.blue()
    )
    embed.add_field(name="+commandes", value="Montre la liste des commandes", inline=False)
    embed.add_field(name=" Plus de commandes d'aides ultérieurement", value="", inline=False)

    await ctx.send(embed=embed)
    
# On sépare les commandes en pages
pages = []

# Page 1 : Commandes staff
embed1 = discord.Embed(
    title="💻 Menu des commandes (Page 1/3)",
    description="Commandes réservées au staff 🛠️:",
    color=discord.Color.green()
)
embed1.add_field(name="+delete [nombre de messages]", value="Supprime le nombre de messages donné", inline=False)
embed1.add_field(name="+ban [user]", value="Bannir un membre, il ne pourra pas revenir dans le serveur.", inline=False)
embed1.add_field(name="+kick [user]", value="Expulser un membre, mais il peut revenir dans le serveur", inline=False)
embed1.add_field(name="+mute [user] [duration]", value="Mettre un membre en sourdine pendant un temps donné", inline=False)
embed1.add_field(name="+unmute [user]", value="Retirer l'action mute d'un membre", inline=False)
embed1.add_field(name="+timeout [user] [duration]", value="Mettre un membre en timeout pendant une durée", inline=False)
embed1.add_field(name="+untimeout [user]", value="Permet à un membre de parler après un timeout", inline=False)
embed1.add_field(name="+warn", value="Avertis un membre d'un comportement inapproprié", inline=False)
embed1.add_field(name="+poll", value="Crée un sondage pour le serveur", inline=False)
pages.append(embed1)

# Page 2 : Commandes administrateur
embed2 = discord.Embed(
    title="💻 Menu des commandes (Page 2/3)",
    description="Commandes réservées à l'administrateur du serveur 💻",
    color=discord.Color.green()
)
embed2.add_field(name="+shutdown", value="Éteins le bot", inline=False)
embed2.add_field(name="+givecoins [user] [amount]", value="Donne de l'argent à un user sans retrait d'argent.", inline=False)
embed2.add_field(name="+ping", value="Annonce le ping du bot", inline=False)
embed2.add_field(name="+start_tournoi", value="Lance le tournoi du jour", inline=False)
embed2.add_field(name="+end_tournoi", value="Termine le tournoi du jour", inline=False)
embed2.add_field(name="COMMANDES POUR LES TOURNOIS:", value="",inline=False)
embed2.add_field(name="+game [mode]", value="Choisit un jeu pour le tournoi (pfc, quiz, pendu ou random)", inline=False)
embed2.add_field(name="+pick", value="Tire au hasard deux joueurs pour un match", inline=False)
embed2.add_field(name="+victoire [user]", value="Déclare une victoire à un joueur (+3 points)", inline=False)
embed2.add_field(name="+defaite [user]", value="Déclare une défaite à un joueur (0 point)", inline=False)
embed2.add_field(name="+egalite [user1] [user2]", value="Déclare une égalité entre deux joueurs (+1 point chacun)", inline=False)
embed2.add_field(name="+panel", value="Affiche le panel du Chef de Tournoi", inline=False)
embed2.add_field(name="+addpoints [user] [points]", value="Ajoute des points à un user", inline=False)
pages.append(embed2)

# Page 3 : Commandes pour tous les membres
embed3 = discord.Embed(
    title="💻 Menu des commandes (Page 3/3)",
    description="Commandes pour tous les membres :",
    color=discord.Color.green()
)
embed3.add_field(name="+mate", value="Envoie une demande de partenaire de jeu aux autres membres", inline=False)
embed3.add_field(name="+userinfo [user]", value="Obtenir les infos d'un utilisateur", inline=False)
embed3.add_field(name="+serverinfo", value="Donne les infos du serveur", inline=False)
embed3.add_field(name="+remind [time]", value="Crée un rappel pour soi dans un temps donné", inline=False)
embed3.add_field(name="+pfc [pierre/feuille/ciseaux]", value="Joue au jeu Pierre-Feuille-Ciseaux contre le bot", inline=False)
embed3.add_field(name="+pendu", value="Démarre une partie de pendu", inline=False)
embed3.add_field(name="+lettre", value="Démarre un quiz", inline=False)
embed3.add_field(name="+quiz", value="Démarre un quiz", inline=False)
embed3.add_field(name="DURANT LES TOURNOIS:", value="", inline=False)
embed3.add_field(name="+join_tournoi", value="Rejoindre le tournoi du jour", inline=False)
embed3.add_field(name="+classement_jour", value="Afficher le classement du jour", inline=False)
embed3.add_field(name="+wiki [sujet]", value="Recherche un sujet sur Wikipédia et vous donne la description", inline=False)
embed3.add_field(name="+trad", value="Choisissez parmi les langues discponibles et traduisez ce que vous voulez", inline=False)
embed3.add_field(name="+money", value="Affiche votre solde de coins", inline=False)
embed3.add_field(name="+daily", value="Réclamez votre récompense quotidienne de coins", inline=False)
embed3.add_field(name="+pay [user] [amount]", value="Payez un autre utilisateur avec vos coins", inline=False)
embed3.add_field(name="+shop", value="Affiche la boutique où vous pouvez acheter des rôles avec vos coins", inline=False)
embed3.add_field(name="+buy [role]", value="Achetez un rôle dans la boutique avec vos coins", inline=False)
embed3.add_field(name="+coinflip [amount] [pile/face]", value="Jouez à pile ou face pour doubler vos coins", inline=False)
embed3.add_field(name="+slots [amount]", value="Jouez aux machines à sous pour gagner des coins", inline=False)
embed3.add_field(name="+blind", value="Participez à un blindtest (UNIQUEMENT DANS DES SALONS VOCAUX)", inline=False)
pages.append(embed3)

# Classe de pagination
class Paginator(View):
    def __init__(self, pages):
        super().__init__(timeout=120)
        self.pages = pages
        self.current = 0
        self.prev_button.disabled = True
        if len(pages) == 1:
            self.next_button.disabled = True

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: Button):
        self.current -= 1
        if self.current == 0:
            button.disabled = True
        self.next_button.disabled = False
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        self.current += 1
        if self.current == len(self.pages) - 1:
            button.disabled = True
        self.prev_button.disabled = False
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

# Commande pour afficher les embeds paginés
@bot.command()
async def commandes(ctx):
    await ctx.send(embed=pages[0], view=Paginator(pages))
    
    
    
# Vérifie si la personne est admin OU a le rôle STAFF 🛠️
def is_staff():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        staff_role = discord.utils.get(ctx.guild.roles, name="[ 🛠️ Staff ] ")
        if staff_role in ctx.author.roles:
            return True
        return False
    return commands.check(predicate)


# -------------------------
# Commande purge
# -------------------------
@bot.command()
@is_staff()
async def delete(ctx, amount: int = 3):
    await ctx.channel.purge(limit=amount + 1)  # +1 pour aussi supprimer la commande de l'utilisateur
    confirmation = await ctx.send(f"🧹 {amount} message(s) supprimé(s) avec succès !")
    await confirmation.delete(delay=5.0)  # Supprimer l’embed après 5 sec

# -------------------------
# Commande kick
# -------------------------
@bot.command()
@is_staff()
async def kick(ctx, member: discord.Member, *, reason="Aucune raison fournie"):
    try:
        await member.send(f"👢 Vous avez été **expulsé** du serveur **{ctx.guild.name}** car {reason}. Mais revenir dans le serveur est toujours possible !")
    except:
        pass
    await member.kick(reason=reason)
    await ctx.send(f"👢 {member.mention} a été éxpulsé du serveur car {reason}. Mais ils peuvent tout de même revenir dans le serveur !")


# -------------------------
# Commande ban
# -------------------------
@bot.command()
@is_staff()
async def ban(ctx, member: discord.Member, *, reason="Aucune raison fournie"):
    try:
        await member.send(f"🔨 Vous avez été **banni** du serveur **{ctx.guild.name}** car {reason}")
    except:
        pass
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member.mention} a été banni du serveur car {reason}")


# -------------------------
# Commande mute
# -------------------------
@bot.command()
@is_staff()
async def mute(ctx, member: discord.Member, *, reason="Aucune raison fournie"):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not role:
        # Création du rôle si inexistant
        role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, send_messages=False, speak=False)

    await member.add_roles(role, reason=reason)

    try:
        await member.send(f"🔇 Vous avez été **Mis en silencieux** sur **{ctx.guild.name}** car {reason}")
    except:
        pass

    await ctx.send(f"🔇 {member.mention} a été mis en silencieux car {reason}")


# -------------------------
# Commande unmute
# -------------------------
@bot.command()
@is_staff()
async def unmute(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if role in member.roles:
        await member.remove_roles(role)
        try:
            await member.send(f"🔊 Vous pouvez désormais **parler** sur **{ctx.guild.name}**.")
        except:
            pass
        await ctx.send(f"🔊 {member.mention} est désormais autorisé à parler ✅")
    else:
        await ctx.send("❌ Ce membre n'a pas reçu de sanction concernant le chat.")


@bot.command()
async def shutdown(ctx):
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ Impossible d'éffectuer cette commande. Vous ne disposez pas des droits pour le faire.")
        return


    await ctx.send("🛑 Le bot s'éteint...")
    await bot.close()


# -------------------------
# Système de mate
# -------------------------
class MateView(View):
    def __init__(self, author):
        super().__init__(timeout=None)
        self.author = author

    @discord.ui.button(label="✅ Oui", style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user == self.author:
            await interaction.response.send_message("❌ C'est tentant mais tu ne peut pas devenir ton propre mate, c'est dommage !", ephemeral=True)
            return
        await interaction.response.send_message(
            f"🎉 {interaction.user.mention} est maintenant le mate de {self.author.mention} ❤️"
        )
        self.stop()

    @discord.ui.button(label="❌ Non", style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user == self.author:
            await interaction.response.send_message("❌ Pourquoi essayer de te refuser ? De toute façon tu ne peut pas !", ephemeral=True)
            return
        await interaction.response.send_message(
            f"{interaction.user.mention} a malheureusement refusé d'être le mate de {self.author.mention} 😢"
        )
        self.stop()


@bot.command()
async def mate(ctx):
    embed = discord.Embed(
        title="🔎 Recherche de Mate",
        description=f"{ctx.author.mention} cherche un mate ! Cliquez sur ✅ ou ❌ pour l'accepter ou le refuser",
        color=discord.Color.blurple()
    )
    view = MateView(ctx.author)
    await ctx.send(embed=embed, view=view)


@bot.command()
@is_staff()
async def timeout(ctx, member: discord.Member, minutes: int, *, reason="Aucune raison fournie"):
    duration = timedelta(minutes=minutes)

    try:
        await member.timeout(duration, reason=reason)
        await ctx.send(f"⏳ {member.mention} a été mis en timeout pendant {minutes} minutes car {reason}")
        await member.send(f"⚠️ Vous avez été timeout de **{ctx.guild.name}**pendant {minutes} minutes car {reason}.")

    except Exception as e:
        await ctx.send(f"❌ Impossible de mettre {member.mention} en timeout : {e}")
        
        
@bot.command()
@is_staff()
async def untimeout(ctx, member: discord.Member):
    try:
        await member.timeout(None)  # Enlève le timeout
        await ctx.send(f"✅ {member.mention} n'est plus en timeout.")
        await member.send(f"⚠️ Vous n'êtes plus timeout de **{ctx.guild.name}**, merci de respecter les règles afin de ne pas être sanctionné dans le futur.")

    except Exception as e:
        await ctx.send(f"❌ Impossible d'enlever le timeout : {e}")

@bot.command()
@is_staff()
async def warn(ctx, member: discord.Member, *, reason="Aucune raison fournie"):
    user_id = member.id
    warns[user_id] = warns.get(user_id, 0) + 1

    await ctx.send(f"⚠️ {member.mention} a reçu un avertissement ! (Total: {warns[user_id]})")

    # Sanctions automatiques
    if warns[user_id] == 3:
        await member.timeout(timedelta(minutes=10), reason="3 warns accumulés")
        await ctx.send(f"⏳ {member.mention} a été mis en timeout 10 minutes (3 warns).")
    elif warns[user_id] == 5:
        await ctx.guild.ban(member, reason="5 warns accumulés")
        await ctx.send(f"🔨 {member.mention} a été banni (5 warns).")
        
@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)  # en ms
    await ctx.send(f"Ping du bot: {latency}ms")

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"Infos sur {member}", color=discord.Color.green())
    embed.add_field(name="ID", value=member.id, inline=False)
    embed.add_field(name="Pseudo", value=member.display_name, inline=False)
    embed.add_field(name="Compte créé le", value=member.created_at.strftime("%d/%m/%Y"), inline=False)
    embed.add_field(name="A rejoint le serveur le", value=member.joined_at.strftime("%d/%m/%Y"), inline=False)
    embed.add_field(name="Rôles", value=", ".join([r.name for r in member.roles if r.name != "@everyone"]), inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"📊 Infos du serveur : {guild.name}", color=discord.Color.purple())
    embed.add_field(name="ID", value=guild.id, inline=False)
    embed.add_field(name="Membres", value=guild.member_count, inline=False)
    embed.add_field(name="Propriétaire", value=guild.owner, inline=False)
    embed.add_field(name="Créé le", value=guild.created_at.strftime("%d/%m/%Y"), inline=False)
    embed.add_field(name="Nombre de rôles", value=len(guild.roles), inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def remind(ctx, temps: int, *, message: str):
    await ctx.send(f"⏰ Je te rappellerai dans {temps} secondes : {message}")
    await asyncio.sleep(temps)
    await ctx.send(f"🔔 Rappel : {ctx.author.mention}, {message}")

@bot.command()
async def poll(ctx, *, question: str):
    embed = discord.Embed(title="📊 Sondage", description=question, color=discord.Color.gold())
    poll_message = await ctx.send(embed=embed)
    await poll_message.add_reaction("✅")
    await poll_message.add_reaction("❌")
    
@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name="Membre")
    if role:
        await member.add_roles(role)
        try:
            await member.send(f"👋 Bienvenue sur **{member.guild.name}** ! Tu as reçu automatiquement le rôle **{role.name}**.")
        except:
            pass
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="vérification")
    if channel:
        msg = await channel.send(f"👋 Bienvenue {member.mention} ! Pour accéder au serveur, clique sur ✅.")
        await msg.add_reaction("✅")

        def check(reaction, user):
            return user == member and str(reaction.emoji) == "✅" and reaction.message.id == msg.id

        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=300.0, check=check)  # 5 min
            role = discord.utils.get(member.guild.roles, name="Membre")
            if role:
                await member.add_roles(role)
                await channel.send(f"✅ {member.mention} a passé la vérification !")
        except:
            await member.kick(reason="Échec de la vérification captcha")
async def send_log(guild, message):
    log_channel = discord.utils.get(guild.text_channels, name="logs")
    if log_channel:
        await log_channel.send(message)

@bot.event
async def on_member_ban(guild, user):
    await send_log(guild, f"🔨 {user} a été banni.")

@bot.event
async def on_member_remove(member):
    await send_log(member.guild, f"👢 {member} a quitté ou a été expulsé.")

@bot.event
async def on_message_delete(message):
    if not message.author.bot:
        await send_log(message.guild, f"🗑️ Message supprimé de {message.author}: {message.content}")



# -----------------
#   JEUX
#---------------------

# -------------------------
# Jeu : Pierre - Feuille - Ciseaux
# -------------------------
@bot.command()
async def pfc(ctx, choix: str):
    choix = choix.lower()
    options = ["pierre", "feuille", "ciseaux"]

    if choix not in options:
        return await ctx.send("❌ Choisis entre `pierre`, `feuille` ou `ciseaux`.")

    bot_choix = random.choice(options)

    if choix == bot_choix:
        result = "🤝 Égalité !"
    elif (choix == "pierre" and bot_choix == "ciseaux") or \
         (choix == "feuille" and bot_choix == "pierre") or \
         (choix == "ciseaux" and bot_choix == "feuille"):
        result = "🎉 Tu as gagné !"
    else:
        result = "😢 Tu as perdu !"

    await ctx.send(f"👉 Tu as choisi **{choix}**\n🤖 Le bot a choisi **{bot_choix}**\n\nRésultat : {result}")


# -------------------------
# Jeu : Pendu
# -------------------------
sessions_pendu = {}

@bot.command()
async def pendu(ctx):
    mot = random.choice(mots_pendu)  # <-- mot pioché dans ton fichier
    affichage = "_" * len(mot)
    essais = 6

    sessions_pendu[ctx.author.id] = {
        "mot": mot,
        "affichage": list(affichage),
        "essais": essais,
        "trouvées": []
    }

    await ctx.send(
        f"🎮 Jeu du pendu commencé !\n"
        f"Mot : {' '.join(sessions_pendu[ctx.author.id]['affichage'])}\n"
        f"Essais restants : {essais}\n"
        f"Tape `+lettre [lettre]` pour jouer."
    )


@bot.command()
async def lettre(ctx, lettre: str):
    if ctx.author.id not in sessions_pendu:
        return await ctx.send("❌ Tu n'as pas de partie en cours. Lance `+pendu`.")

    game = sessions_pendu[ctx.author.id]

    if lettre in game["trouvées"]:
        return await ctx.send("❌ Lettre déjà proposée.")

    game["trouvées"].append(lettre)

    if lettre in game["mot"]:
        for i, l in enumerate(game["mot"]):
            if l == lettre:
                game["affichage"][i] = lettre
    else:
        game["essais"] -= 1

    mot_affiche = " ".join(game["affichage"])

    if "_" not in game["affichage"]:
        del sessions_pendu[ctx.author.id]
        return await ctx.send(f"🎉 Bravo {ctx.author.mention}, tu as trouvé le mot : **{mot_affiche}**")

    if game["essais"] <= 0:
        mot_secret = game["mot"]
        del sessions_pendu[ctx.author.id]
        return await ctx.send(f"💀 Perdu {ctx.author.mention} ! Le mot était : **{mot_secret}**")

    await ctx.send(f"Mot : {mot_affiche}\nEssais restants : {game['essais']}")


# -------------------------
# Jeu : Quiz
# -------------------------


quiz_sessions = {}

@bot.command()
async def quiz(ctx):
    q = random.choice(questions_quiz)
    quiz_sessions[ctx.author.id] = q
    await ctx.send(f"❓ {q['question']}\nRéponds avec `+reponse <ta réponse>`")

@bot.command()
async def reponse(ctx, *, rep: str):
    if ctx.author.id not in quiz_sessions:
        return await ctx.send("❌ Tu n'as pas de quiz en cours. Lance `+quiz`.")

    q = quiz_sessions[ctx.author.id]
    if rep.lower() == q["réponse"]:
        del quiz_sessions[ctx.author.id]
        return await ctx.send(f"✅ Bravo {ctx.author.mention}, bonne réponse !")
    else:
        return await ctx.send(f"❌ Mauvaise réponse {ctx.author.mention}. Essaie encore !")
# -------------
#   TOURNOIS 
# -------------

import json
import random
from datetime import datetime

# -------------------------
# Config fichiers sauvegarde
# -------------------------
TOURNOI_FILE = "tournois.json"
RANGS_FILE = "rangs.json"

def load_data(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

tournois = load_data(TOURNOI_FILE)
rangs = load_data(RANGS_FILE)

# -------------------------
# Rôles & paliers
# -------------------------
RANGS_PALIERS = {
    2: "Bronze",
    5: "Argent",
    8: "Or",
    15: "Diamant",
    20: "Légendaire",
    30: "Imbattable"
}

def is_chef():
    async def predicate(ctx):
        return ctx.author.id == OWNER_ID
    return commands.check(predicate)

# -------------------------
# Commandes du Chef de tournoi
# -------------------------

@bot.command()
@is_chef()
async def start_tournoi(ctx):
    """Créer un tournoi du jour"""
    today = datetime.now().strftime("%Y-%m-%d")
    if today in tournois:
        return await ctx.send("❌ Un tournoi est déjà en cours aujourd'hui.")

    tournois[today] = {"participants": {}, "matches": []}
    save_data(TOURNOI_FILE, tournois)
    await ctx.send("🏆 Tournoi du jour lancé ! Les joueurs peuvent s'inscrire avec `+join_tournoi`.")

@bot.command()
@is_chef()
async def end_tournoi(ctx):
    """Terminer le tournoi du jour"""
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in tournois:
        return await ctx.send("❌ Aucun tournoi en cours.")

    await ctx.send("⏹️ Le tournoi est terminé ! Utilise `+classement_jour` pour afficher les résultats.")

@bot.command()
@is_chef()
async def game(ctx, mode: str = "random"):
    """Choisir un jeu pour le tournoi"""
    jeux_dispos = ["pfc", "quiz", "pendu"]
    if mode == "random":
        mode = random.choice(jeux_dispos)

    if mode not in jeux_dispos:
        return await ctx.send(f"❌ Jeu inconnu. Choisis parmi : {', '.join(jeux_dispos)}")

    await ctx.send(f"🎮 Jeu sélectionné : **{mode.upper()}** ! Préparez-vous...")

@bot.command()
@is_chef()
async def pick(ctx):
    """Tirer deux joueurs au hasard pour un match"""
    today = datetime.now().strftime("%Y-%m-%d")
    participants = list(tournois.get(today, {}).get("participants", {}).keys())
    if len(participants) < 2:
        return await ctx.send("❌ Pas assez de joueurs inscrits.")

    joueurs = random.sample(participants, 2)
    await ctx.send(f"⚔️ Match du tournoi : <@{joueurs[0]}> VS <@{joueurs[1]}> !")

# -------------------------
# Commandes : déclarer résultats (donne aussi des coins)
# -------------------------
@bot.command()
@is_chef()
async def victoire(ctx, member: discord.Member):
    await addpoints(ctx, member, 3)  # 3 points tournoi
    update_coins(member.id, 10)      # 10 coins économie
    await ctx.send(f"🏆 Victoire attribuée à {member.mention} (+3 pts, +10💰)")

@bot.command()
@is_chef()
async def defaite(ctx, member: discord.Member):
    await addpoints(ctx, member, 0)  # 0 points tournoi
    update_coins(member.id, 0)       # 0 coin
    await ctx.send(f"💀 Défaite attribuée à {member.mention} (0 pt, 0💰)")

@bot.command()
@is_chef()
async def egalite(ctx, member1: discord.Member, member2: discord.Member):
    await addpoints(ctx, member1, 1)  # 1 point tournoi
    await addpoints(ctx, member2, 1)
    update_coins(member1.id, 3)       # 3 coins chacun
    update_coins(member2.id, 3)
    await ctx.send(f"🤝 Égalité entre {member1.mention} et {member2.mention} (+1 pt, +3💰 chacun)")

# -------------------------
# Commandes joueurs
# -------------------------

@bot.command()
async def join_tournoi(ctx):
    """Rejoindre le tournoi"""
    today = datetime.now().strftime("%Y-%m-%d")

    if today not in tournois:
        return await ctx.send("❌ Aucun tournoi n'est actif aujourd'hui.")

    if str(ctx.author.id) in tournois[today]["participants"]:
        return await ctx.send("❌ Tu es déjà inscrit au tournoi du jour.")

    tournois[today]["participants"][str(ctx.author.id)] = {
        "pseudo": ctx.author.name,
        "points": 0
    }
    save_data(TOURNOI_FILE, tournois)

    await ctx.send(f"✅ {ctx.author.mention} a rejoint le tournoi du jour !")

@bot.command()
async def addpoints(ctx, member: discord.Member, points: int):
    """Ajouter des points à un joueur (utilisé par chef ou mini-jeux)"""
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in tournois or str(member.id) not in tournois[today]["participants"]:
        return await ctx.send("❌ Ce joueur ne participe pas au tournoi du jour.")

    tournois[today]["participants"][str(member.id)]["points"] += points
    save_data(TOURNOI_FILE, tournois)
    await ctx.send(f"➕ {points} points ajoutés à {member.mention}")

@bot.command()
async def classement_jour(ctx):
    """Afficher le classement du jour"""
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in tournois or not tournois[today]["participants"]:
        return await ctx.send("❌ Aucun tournoi actif aujourd'hui.")

    participants = tournois[today]["participants"]
    classement = sorted(participants.items(), key=lambda x: x[1]["points"], reverse=True)
    tournois[today]["classement"] = classement
    save_data(TOURNOI_FILE, tournois)

    msg = "🏆 Classement du jour :\n"
    for i, (user_id, data) in enumerate(classement[:10], start=1):
        msg += f"{i}. {data['pseudo']} ({data['points']} pts)\n"

        # Attribution rang si podium
        if i <= 3:
            await update_rang(ctx.guild, int(user_id), i)

    await ctx.send(msg)

# -------------------------
# Attribution des rangs
# -------------------------

async def update_rang(guild, user_id, place):
    user = guild.get_member(user_id)
    if not user:
        return

    rang_info = rangs.get(str(user_id), {"pseudo": user.name, "podiums_consecutifs": 0, "rang": "Aucun"})

    if place <= 3:
        rang_info["podiums_consecutifs"] += 1
    else:
        rang_info["podiums_consecutifs"] = 0

    new_rang = rang_info["rang"]
    for palier, nom in RANGS_PALIERS.items():
        if rang_info["podiums_consecutifs"] >= palier:
            new_rang = nom

    if new_rang != rang_info["rang"]:
        old_role = discord.utils.get(guild.roles, name=rang_info["rang"])
        new_role = discord.utils.get(guild.roles, name=new_rang)
        if not new_role:
            new_role = await guild.create_role(name=new_rang)

        if old_role in user.roles:
            await user.remove_roles(old_role)
        await user.add_roles(new_role)
        await user.send(f"🎉 Félicitations {user.name}, tu viens d'obtenir le rang **{new_rang}** !")

    rang_info["rang"] = new_rang
    rangs[str(user_id)] = rang_info
    save_data(RANGS_FILE, rangs)
@bot.command()
@is_chef()
async def panel(ctx):
    embed = discord.Embed(
        title="🎮 Panel du Chef de Tournoi",
        description="Utilise les boutons ci-dessous pour gérer ton tournoi",
        color=discord.Color.gold()
    )
    embed.add_field(name="⚙️ Gestion", value="Start / End / Pick joueurs", inline=False)
    embed.add_field(name="📊 Classement", value="Afficher le classement du jour", inline=False)
    embed.set_footer(text="Seul le Chef (toi) peut utiliser ce panel ⚔️")

    view = PanelTournoi(ctx.author)
    await ctx.send(embed=embed, view=view)

    

class PanelTournoi(View):
    def __init__(self, author):
        super().__init__(timeout=None)
        self.author = author  # Chef du tournoi

    async def interaction_check(self, interaction):
        # Bloque les autres utilisateurs
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Epepep, tu n'es pas le Chef du tournoi, tu ne peut pas toucher à ces comandes !", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="⚙️ Commencer un Tournoi", style=discord.ButtonStyle.green)
    async def start(self, interaction, button):
        await start_tournoi(interaction)  # appelle ta commande existante
        await interaction.response.send_message("🏆 Tournoi lancé !", ephemeral=True)

    @discord.ui.button(label="⏹️ Terminer un Tournoi", style=discord.ButtonStyle.red)
    async def end(self, interaction, button):
        await end_tournoi(interaction)
        await interaction.response.send_message("⏹️ Tournoi terminé !", ephemeral=True)

    @discord.ui.button(label="🎲 Pick joueurs", style=discord.ButtonStyle.blurple)
    async def pick(self, interaction, button):
        await pick(interaction)
        await interaction.response.send_message("⚔️ Joueurs tirés au sort !", ephemeral=True)

    @discord.ui.button(label="📊 Classement", style=discord.ButtonStyle.gray)
    async def classement(self, interaction, button):
        await classement_jour(interaction)
        await interaction.response.send_message("📊 Classement du jour affiché", ephemeral=True)


CHANNEL_GENERAL = 1408795790515634297  # 💬 general-tournois
CHANNEL_GAGNANTS = 1408795241003352126  # 🏆 gagnants-du-jour
CHANNEL_PLANNING = 1408795407336865832  # 📅 organisation-et-planning
CHANNEL_REGLEMENT = 1408795561213296691  # 📜 reglement

@tasks.loop(minutes=1)
async def tournoi_annonce():
    now = datetime.now().strftime("%H:%M")
    if now == "19:28":  # tous les jours à 19h
        today = datetime.now().strftime("%Y-%m-%d")
        if today in tournois and "participants" in tournois[today]:
            channel = bot.get_channel(CHANNEL_GAGNANTS)
            participants = tournois[today]["participants"]
            classement = sorted(participants.items(), key=lambda x: x[1]["points"], reverse=True)

            msg = f"🏆 **Classement du {today}** 🏆\n\n"
            for i, (user_id, data) in enumerate(classement[:10], start=1):
                msg += f"{i}. {data['pseudo']} ({data['points']} pts)\n"

            await channel.send(msg)
            
@tasks.loop(minutes=1)
async def planning_annonce():
    now = datetime.now().strftime("%H:%M")
    if now == "19:29":  # tous les jours à 10h
        channel = bot.get_channel(CHANNEL_PLANNING)
        await channel.send("📅 Le tournoi du jour commencera à **15h00** ! Préparez-vous ⚔️")

@bot.event
async def on_ready():
    tournoi_annonce.start()
    print("✅ Bot prêt et système tournoi activé")








@bot.command()
async def wiki(ctx, *, query: str):
    """Recherche un résumé sur Wikipedia"""
    try:
        page = wikipedia.page(query)
        summary = wikipedia.summary(query, sentences=3)

        embed = discord.Embed(
            title=f"Wikipedia : {page.title}",
            url=page.url,
            description=summary,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    except wikipedia.exceptions.DisambiguationError as e:
        await ctx.send(f"⚠️ Plusieurs résultats possibles : {', '.join(e.options[:5])}...")
    except wikipedia.exceptions.PageError:
        await ctx.send("❌ Aucun article trouvé.")




LANGUES = {
    "fr": "Français",
    "en": "Anglais",
    "es": "Espagnol",
    "de": "Allemand",
    "it": "Italien",
    "pt": "Portugais",
    "ru": "Russe",
    "ja": "Japonais",
    "zh-cn": "Chinois simplifié",
    "ar": "Arabe"
}

class TradView(View):
    def __init__(self, author):
        super().__init__(timeout=60)
        self.author = author

        options = [discord.SelectOption(label=nom, value=code) for code, nom in LANGUES.items()]
        self.add_item(Select(placeholder="Choisis une langue cible", options=options))

    async def interaction_check(self, interaction):
        return interaction.user == self.author

    @discord.ui.select(placeholder="Choisis une langue cible", options=[discord.SelectOption(label=nom, value=code) for code, nom in LANGUES.items()])
    async def select_langue(self, interaction, select):
        langue = select.values[0]
        await interaction.response.send_message(
            f"📝 Écris maintenant ton message à traduire → il sera traduit en **{LANGUES[langue]}**.\n"
            f"Réponds à ce message dans les **60 secondes**.",
            ephemeral=True
        )

        def check(m):
            return m.author == self.author and m.channel == interaction.channel

        try:
            message = await bot.wait_for("message", check=check, timeout=60)
            traduction = GoogleTranslator(source="auto", target=langue).translate(message.content)

            embed = discord.Embed(
                title="🌍 Traduction",
                description=f"**Texte original :** {message.content}\n\n**Traduction ({LANGUES[langue]}):** {traduction}",
                color=discord.Color.green()
            )
            await interaction.channel.send(embed=embed)

        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Temps écoulé, recommence avec `+trad`.", ephemeral=True)

@bot.command()
async def trad(ctx):
    """Interface interactive de traduction"""
    embed = discord.Embed(
        title="🌍 Traduction interactive",
        description="Choisis la langue cible dans le menu ci-dessous.",
        color=discord.Color.blue()
    )
    view = TradView(ctx.author)
    await ctx.send(embed=embed, view=view)



# -----------------------------
#       ÉCONOMIE DU BOT
# -----------------------------

ECONOMY_FILE = "economy.json"

def load_economy():
    try:
        with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_economy():
    with open(ECONOMY_FILE, "w", encoding="utf-8") as f:
        json.dump(economy, f, indent=2, ensure_ascii=False)

economy = load_economy()

# -----------------------------
#  Commande : voir ses coins
# -----------------------------
@bot.command(aliases=["coins", "balance"])
async def money(ctx, member: discord.Member = None):
    member = member or ctx.author
    user_id = str(member.id)

    coins = economy.get(user_id, {}).get("coins", 0)
    await ctx.send(f"💰 {member.display_name} possède **{coins} coins**.")

# -----------------------------
#  Fonction utilitaire : donner/retirer coins
# -----------------------------
def update_coins(user_id, amount):
    if str(user_id) not in economy:
        economy[str(user_id)] = {"coins": 0}
    economy[str(user_id)]["coins"] += amount
    if economy[str(user_id)]["coins"] < 0:
        economy[str(user_id)]["coins"] = 0
    save_economy()

# -----------------------------
#  Commande admin : givecoins
# -----------------------------
@bot.command()
@commands.has_permissions(administrator=True)
async def givecoins(ctx, member: discord.Member, amount: int):
    update_coins(member.id, amount)
    await ctx.send(f"✅ {member.mention} a reçu **{amount} coins**.")

# -----------------------------
#  Boutique
# -----------------------------
SHOP = {
    
    "Billet de 10RM$": {"price": 10, "role": None, "desc": "Rien de spécial, vous avez juste un billet :)"},
    "Billet de 20RM$": {"price": 20, "role": None, "desc": "Toujours rien de spécial, vous pouvez juste flex :)"},
    "Billet de 100RM$": {"price": 100, "role": None, "desc": "Mais il n'y a rien de spécial à avoir avec ces billets, c'est juste fait pour frimer..."},
    "Billet de 200RM$": {"price": 200, "role": None, "desc": "Mais tu est Elon Musk pour avoir autant d'argent à dépenser ?"},
    "Billet de 500RM$": {"price": 500, "role": None, "desc": "Non mais ça va s'arrêter quand ?"},
    "Rôle VIP": {"price": 750, "role": 1408221998848544878, "desc": "Accès à un salon privé et quelques avantages. Oui c'est cher, mais ça vaut le coup, promis."},
    "Rôle Premium": {"price": 1000, "role": 1413822835524112505, "desc": "Alors la tu veut vraiment être au dessus des autres en fait ._."}


}

@bot.command()
async def shop(ctx):
    embed = discord.Embed(title="🛒 Boutique du serveur", color=discord.Color.green())
    for item, data in SHOP.items():
        desc = data.get("desc", "")
        prix = data["price"]
        role = f"(Rôle : {data['role']})" if data.get("role") else ""
        embed.add_field(name=item, value=f"Prix : {prix} 💰 {role} {desc}", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def buy(ctx, *, item: str):
    user_id = str(ctx.author.id)
    if item not in SHOP:
        return await ctx.send("❌ Cet objet n'existe pas dans la boutique.")

    prix = SHOP[item]["price"]
    if economy.get(user_id, {}).get("coins", 0) < prix:
        return await ctx.send("❌ Tu n'as pas assez de coins.")

    # Déduire le prix
    update_coins(ctx.author.id, -prix)

    # Si c'est un rôle
    role_name = SHOP[item].get("role")
    if role_name:
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            role = await ctx.guild.create_role(name=role_name)
        await ctx.author.add_roles(role)
        await ctx.send(f"✅ Tu as acheté le rôle **{role_name}** !")

    else:
        await ctx.send(f"✅ Tu as acheté **{item}** !")

import random

# -------------------------
# 🎲 Coinflip
# -------------------------
@bot.command()
async def coinflip(ctx, choix: str, mise: int):
    """Pile ou face avec mise de coins"""
    choix = choix.lower()
    if choix not in ["pile", "face"]:
        return await ctx.send("❌ Choisis entre `pile` ou `face`.")

    user_id = str(ctx.author.id)
    if economy.get(user_id, {}).get("coins", 0) < mise:
        return await ctx.send("❌ Tu n'as pas assez de coins.")

    # Tirage
    resultat = random.choice(["pile", "face"])
    if choix == resultat:
        gain = mise
        update_coins(ctx.author.id, gain)
        await ctx.send(f"🎉 C'est **{resultat}** ! Tu as gagné **+{gain}💰**.")
    else:
        update_coins(ctx.author.id, -mise)
        await ctx.send(f"💀 C'est **{resultat}**... Tu perds **-{mise*2}💰**.")

# -------------------------
# 🎰 Slots
# -------------------------
@bot.command()
async def slots(ctx, mise: int):
    """Machine à sous avec mise de coins"""
    user_id = str(ctx.author.id)
    if economy.get(user_id, {}).get("coins", 0) < mise:
        return await ctx.send("❌ Tu n'as pas assez de coins.")

    emojis = ["🍒", "🍋", "🔔", "⭐", "7️⃣"]
    tirage = [random.choice(emojis) for _ in range(3)]

    msg = f"🎰 | {' | '.join(tirage)} | 🎰\n"
    gain = 0

    if len(set(tirage)) == 1:  # 3 identiques
        gain = mise * 5
        msg += f"🎉 JACKPOT ! Tu gagnes **{gain}💰**"
    elif len(set(tirage)) == 2:  # 2 identiques
        gain = mise * 2
        msg += f"✨ Deux symboles identiques ! Tu gagnes **{gain}💰**"
    else:
        gain = -mise
        msg += f"💀 Rien... Tu perds **{mise}💰**"

    update_coins(ctx.author.id, gain)
    await ctx.send(msg)


import asyncio

FFMPEG_OPTIONS = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}


vc_sessions = {}
def load_blindlist():
    with open("blindlist.txt", "r", encoding="utf-8") as f:
        return [line.strip().split(";") for line in f.readlines()]

@bot.command()
async def blind(ctx):
    if not ctx.author.voice:
        return await ctx.send("❌ Tu dois être dans un salon vocal.")
    channel = ctx.author.voice.channel

    try:
        # Vérifie si le bot est déjà connecté
        if ctx.voice_client:
            vc = ctx.voice_client
        else:
            vc = await channel.connect()
    except Exception as e:
        await ctx.send(f"❌ Impossible de se connecter au vocal : {e}")
        return

    vc_sessions[ctx.guild.id] = vc  # Stocke la connexion

    music_dir = "Musics"
    fichier = os.path.join(music_dir, random.choice(os.listdir(music_dir)))
    await ctx.send(f"🎵 Musique jouée : **{os.path.basename(fichier)}**")
    
    try:
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(fichier), volume=VOLUME)
        vc.play(source)
    except Exception as e:
        await ctx.send(f"❌ Impossible de jouer la musique : {e}")
        await vc.disconnect()
        vc_sessions.pop(ctx.guild.id, None)
        return

    while vc.is_playing():
        await asyncio.sleep(1)
    await vc.disconnect()
    vc_sessions.pop(ctx.guild.id, None)

    # Charger une musique
    musiques = load_blindlist()
    fichier, titre = random.choice(musiques)
    await ctx.send(musiques)


    await ctx.send("🎵 Blind Test lancé ! Devine la musique en moins de **30 secondes** !")
    titre_simple = titre.split(" - ")[-1].strip().lower()
    # Vérifier les réponses
    def check(m):
        return m.channel == ctx.channel and not m.author.bot

    winner = None
    try:
        while True:
            msg = await bot.wait_for("message", timeout=30, check=check)
        # Vérifie si la réponse contient le titre complet ou juste le titre
            if titre.lower() in msg.content.lower() or titre_simple in msg.content.lower():
                winner = msg.author
                break
    except asyncio.TimeoutError:
        pass

    vc.stop()
    await asyncio.sleep(1)
    await vc.disconnect()

    if winner:
        update_coins(winner.id, 15)
        await ctx.send(f"🏆 {winner.mention} a trouvé ! C’était **{titre}** (+15💰)")
    else:
        await ctx.send(f"⏱️ Temps écoulé ! La réponse était : **{titre}**")
@bot.command()
async def stop(ctx):
    """Arrête la musique et déconnecte le bot du vocal"""
    vc = vc_sessions.get(ctx.guild.id)
    if vc and vc.is_connected():
        vc.stop()
        await vc.disconnect()
        vc_sessions.pop(ctx.guild.id, None)
        await ctx.send("⏹️ Musique arrêtée et bot déconnecté du vocal.")
    else:
        await ctx.send("❌ Aucune musique en cours ou bot non connecté.")

@bot.command()
async def restart(ctx):
    """Relance le blindtest dans le salon vocal"""
    vc = vc_sessions.get(ctx.guild.id)
    if vc and vc.is_playing():
        vc.stop()
        await asyncio.sleep(1)  # Laisse le temps à ffmpeg de s'arrêter
    if not ctx.author.voice:
        return await ctx.send("❌ Tu dois être dans un salon vocal.")
    await ctx.invoke(bot.get_command("blind"))
@bot.command()
async def volume(ctx, value: float):
    """Règle le volume du blindtest (0.0 à 2.0)"""
    global VOLUME
    if not (0.0 <= value <= 2.0):
        return await ctx.send("❌ Le volume doit être entre 0.0 et 2.0.")
    VOLUME = value
    await ctx.send(f"🔊 Volume réglé à {int(VOLUME*100)}%")
# ------------------------- 
# Quand le bot est prêt 
# ------------------------- 
@bot.event 
async def on_ready(): 
    latency = round(bot.latency * 1000) 
    print(f"✅ Bot connecté. ID: {bot.user}") 
    print(f" Ping: {latency}ms") 
    
# ------------------------- 
# Lancer le bot 
# ------------------------- 
if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)