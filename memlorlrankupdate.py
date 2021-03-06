import discord
from discord.ext import commands
import rls
from rls.rocket import RocketLeague
import json
import ast
from .utils import checks
import urllib
import pprint

class memlorlrank:
        """Custom cog by Memlo and Eny, Matt Miller and Patrik Srna, that retrieves a user's Rocket League rank based on gamertag and platform input and sets a role"""

        def __init__(self, bot):
                self.bot = bot
                self.image = "data/rlstats/signature.png"
                self.json = "data/rlstats/rlstats.json"
                self.legend = "data/rlstats/tierlegend.json"
                self.apikey = "data/rlstats/rls-api.json"

        @commands.command(pass_context=True)
        async def rlrankupdate(self, ctx, platform, *, gamertag : str):
                """Find your RL stats and get your role updated to match your rank"""
                server = ctx.message.server
                channel = ctx.message.channel
                author = str(ctx.message.author)
                latestseason = "7"
                acceptedplatforms = ['pc', 'ps4', 'xbox']
                #reverse error handling for easier understanding
                if platform.lower() not in acceptedplatforms:
                        await self.discordsay("I'm pretty sure `" + platform + "` is not a real console.")
                else:
                        returndata = self.getrank(platform.lower(), gamertag)
                        if "Fail" in returndata:
                                await self.discordsay(returndata)
                        else:
                                ranks =[]
                                for k,v in returndata.items():
                                        if latestseason == k:
                                                allranks = v
                                                if '10' in allranks:
                                                        ranks.append(allranks['10']['tier'])
                                                if '11' in allranks:
                                                        ranks.append(allranks['11']['tier'])
                                                if '12' in allranks:
                                                        ranks.append(allranks['12']['tier'])
                                                if '13' in allranks:
                                                        ranks.append(allranks['13']['tier'])
                                                break
#                               when done like this the error throws after each loop where latestseason != k... need to think this one through
#                               else:
#                                       await self.discordsay("There wasn't any information regarding the latest season.")    
                                try:
                                        allranks
                                except NameError:
                                        await self.discordsay("I had trouble finding information about you on rocketleaguestats.com") 
                                else:
                                        maxrankint = str(max(ranks))
                                        await self.discordsendfile(channel, self.image)
                                        if "0" in maxrankint:
                                                await self.discordsay("Looks like you need to play some ranked games for me to set your rank.")
                                        else:
                                                maxrank = self.matchtier(maxrankint)
                                                await self.discordsay("Your highest rank in season `" + latestseason + "` is `" + maxrank + "`.")
                                                #match user roles to server roles and remove old rank
                                                #<code>
                                                #set new rank                                                
                                                applyrole = self.member_apply_role(server, author, maxrank)
                                                await self.discordsay(applyrole)

        def getrank(self, platform, gamertag):
                """Retrieves Rocket League Stats image from rocketleaguestats.com using their API sends image back"""
                apikey = self.parsejson(self.apikey)[1] #call the API key from json file
                rocket = RocketLeague(api_key=apikey)
                platformlegend = {'pc' : 1, 'ps4' : 2, 'xbox' : 3}
                for k,v in platformlegend.items(): #using the platform legend, find the platform ID
                        if platform == k:
                                platformid = v
                                break
                try:
                        platformid
                except NameError:
                        return "getrank NameError - ask an admin"
                else:
                        try:
                                playerdata = rocket.players.player(id=gamertag, platform=platformid) #use the gamertag and platform ID to find the json formatted player data
                        except rls.exceptions.ResourceNotFound:
                                error = "Fail. There was an issue finding your gamertag in the <http://rocketleaguestats.com/> database."
                                return error
                        else:
                                rank = playerdata.json()['rankedSeasons']
                                with open(self.json, "w") as f: #save the json to a file for later (might not need to do this)
                                        json.dump(playerdata.json(), f)
                                opener=urllib.request.build_opener() #download and save the rocket league signature image
                                opener.addheaders=[('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
                                urllib.request.install_opener(opener)
                                urllib.request.urlretrieve(playerdata.json()['signatureUrl'], self.image)
                                if "displayName" in playerdata.json():
                                        return rank
                                elif "code" in playerdata.json():
                                        error = "Fail. Error: " + playerdata.json()['code'] + ". " + playerdata.json()['message']
                                        return error
                                else:
                                        return "Fail.  Not sure how we got here."

        def parsejson(self, file):
                """Take a json file and return dictionary"""
                with open(file, 'r') as f:
                        data = f.read()
                        data_dict = ast.literal_eval(data)
                        return data_dict

        def matchtier(self, rankint):
                """Using the RL Tier Legend, change the rankint into namedrank"""
                legend = self.parsejson(self.legend) #parse the legend json file
                for k,v in legend.items(): #loop through to find the rankint
                        if rankint == k:
                                namedrank = v
                                break
                try:
                        namedrank
                except NameError:
                        error = "Fail. Welp, a NameError occurred when looking at ranks"
                        return error
                else:
                        return namedrank

        async def discordsay(self, data):
                """Simple text in discord"""
                await self.bot.say(data)

        async def discordsendfile(self, channel, file):
                """Simple attachment in discord"""
                await self.bot.send_file(channel, file)



        async def server_has_role(self, server, role):
                if role in [role.name for role in server.roles]:
                        return True
                return False

        async def server_get_role(self, server, role):
                if await self.server_has_role(server, role):
                        return [r for r in server.roles if r.name == role][0]
                return False

        async def member_apply_role(self, server, member, role):
                if await self.bot_has_role(server, role) and await self.server_has_role(server, role):
                        try:
                                role = await self.server_get_role(server, role)
                                await self.bot.add_roles(member, role)
                                return "Completed"
                        except discord.Forbidden:
                                return "Not Completed"
                        else:
                                return "Completed"

        async def member_remove_role(self, server, member, role):
                if await self.bot_has_role(server, role) and await self.server_has_role(server, role):
                        try:
                                role = await self.server_get_role(server, role)
                                await self.bot.remove_roles(member, role)
                                return 0
                        except discord.Forbidden:
                                return 2
                        else:
                                return 1

def setup(bot):
        action = memlostats(bot)
        bot.add_cog(action)