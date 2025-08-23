import discord
from discord.ext import commands
from discord.ui import View, Button
from datetime import timedelta
import asyncio
import random
import random
import re
import json

with open("questions.json", "r", encoding="utf-8") as f:
    questions_quiz = json.load(f)



# Liste noire de mots interdits (à compléter si besoin)

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
    
@bot.command()
async def commandes(ctx):
    embed = discord.Embed(
        title="💻 Menu des commandes",
        description="Voici la liste des commandes disponibles :",
        color=discord.Color.green()
    )
    embed.add_field(name="Commandes réservées au staff 🛠️:", value="", inline=False)
    embed.add_field(name="+delete [nombre de messages]", value="Supprime le nombre de messages donné", inline=False)
    embed.add_field(name="+ban [user]", value="Bannir un membre, il ne pourra pas revenir dans le serveur. Pour le débannir, aller dans les PAramètres du serveur", inline=False)
    embed.add_field(name="+kick [user]", value="Expulser un membre, mais il peut toutefois revenir dans le serveur", inline=False)
    embed.add_field(name="+mute [user] [duration]", value="Mettre en sourdine un membre, il ne pourra plus parler pendant le temps indiqué", inline=False)
    embed.add_field(name="+unmute [user]", value="Retirer l'action mute d'un membre.", inline=False)
    embed.add_field(name="+timeout [user] [duration]",  value="Ajoute un timeout à un membre pendant la durée indiqué, il ne pourra pas envoyer de message durant le timeout", inline=False)
    embed.add_field(name="+untimeout [user]", value="Permet au membre qui a prit un timeout de pouvoir renvoyer des messages.", inline=False)
    embed.add_field(name="+warn", value="Avertis un membre d'un comportement inaproprié", inline=False)
    embed.add_field(name="+poll", value="Crée un sondage pour le serveur", inline=False)
    
    embed.add_field(name="Commandes résérvées à l'administrateur du serveur 💻", value="", inline=False)
    embed.add_field(name="+shutdown", value="Eteins le bot", inline=False)
    embed.add_field(name="+ping", value="Annonce le ping du bot", inline=False)
    
    embed.add_field(name="Commandes pour tous les membres:",value="", inline=False)
    embed.add_field(name="+mate", value="Envoie une demande de partenaire de jeu aux autres membres, ceux-cis peuvent accepter ou refuser", inline=False)
    embed.add_field(name="+userinfo [user]", value="Obtenir les infos d'un utilisateur", inline=False)
    embed.add_field(name="+serverinfo", value="Donne les infos du serveur", inline=False)
    embed.add_field(name="+remind [time]", value="Crée un rappel pour soi dans un temps donné", inline=False)
    embed.add_field(name=" Plus de commandes d'aides ultérieurement", value="", inline=False)#mate, userinfo, serverinfo, remind

    await ctx.send(embed=embed)



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


# -------------------------
# Commande shutdown
# -------------------------
OWNER_ID = "YOUR_OWNER_ID"

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
import random

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
from discord.ext import commands

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

@bot.command()
@is_chef()
async def victoire(ctx, member: discord.Member):
    """Déclarer une victoire"""
    await addpoints(ctx, member, 3)
    await ctx.send(f"🏆 Victoire attribuée à {member.mention} (+3 pts)")

@bot.command()
@is_chef()
async def defaite(ctx, member: discord.Member):
    """Déclarer une défaite"""
    await addpoints(ctx, member, 0)
    await ctx.send(f"💀 Défaite attribuée à {member.mention} (0 pts)")

@bot.command()
@is_chef()
async def egalite(ctx, member1: discord.Member, member2: discord.Member):
    """Déclarer une égalité"""
    await addpoints(ctx, member1, 1)
    await addpoints(ctx, member2, 1)
    await ctx.send(f"🤝 Égalité entre {member1.mention} et {member2.mention} (+1 pt chacun)")

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

    
from discord.ui import View, Button

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


CHANNEL_GENERAL = "GENERALCHANNEL"  
CHANNEL_GAGNANTS = "WINNERSCHANNEL"  # 🏆 gagnants-du-jour
CHANNEL_PLANNING = "PLANNINGCHANNEL"  # 📅 organisation-et-planning
CHANNEL_REGLEMENT = "RULESCHANNEL"  # 📜 reglement
from discord.ext import tasks

@tasks.loop(minutes=1)
async def tournoi_annonce():
    now = datetime.now().strftime("%H:%M")
    if now == "19:00":  # tous les jours à 19h
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
    if now == "10:00":  # tous les jours à 10h
        channel = bot.get_channel(CHANNEL_PLANNING)
        await channel.send("📅 Le tournoi du jour commencera à **15h00** ! Préparez-vous ⚔️")

@bot.event
async def on_ready():
    tournoi_annonce.start()
    print("✅ Bot prêt et système tournoi activé")


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

bot.run("YOUR_BOT_ID")