import discord
from discord.ext import commands
from discord.ui import View, Button

# -------------------------
# Configuration des intents
# -------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="+", intents=intents)
bot.remove_command("help")

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
        color=discord.Color.blue()
    )
    embed.add_field(name="Commandes réservées au staff :", value="Montre la liste des commandes", inline=False)

    embed.add_field(name="+commandes", value="Montre la liste des commandes", inline=False)
    embed.add_field(name=" Plus de commandes d'aides ultérieurement", value="...", inline=False)

    await ctx.send(embed=embed)



# Vérifie si la personne est admin OU a le rôle STAFF 🛠️
def is_staff():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        staff_role = discord.utils.get(ctx.guild.roles, name="STAFF 🛠️")
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
OWNER_ID = "YourOwnerID (Don't forget to delete those thigs at the start and end, or it will not work, believe me i did this mistake)"

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


# -------------------------
# Quand le bot est prêt
# -------------------------
@bot.event
async def on_ready():
    print(f"✅ Bot connecté. ID: {bot.user}")


# -------------------------
# Lancer le bot
# -------------------------
bot.run("YourBotID")