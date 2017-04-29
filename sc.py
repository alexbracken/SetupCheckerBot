import praw
import time

username = ''
password = ''
admin = ''
mods = []
clientid = ''
clientsecret = ''
version = ''
userAgent = ''
subreddit = ''
footer = '\n\n---\n\n*bleep bloop I\'m a bot*\n\nIf you have a specific question, you won\'t get an answer by PMming me. I only check setup posts. Please direct questions to [the moderators of /r/iOSthemes](https://www.reddit.com/message/compose?to=%2Fr%2FiOSthemes).'
removalPM = 'Hello! Thank you for posting a setup to /r/iOSthemes. However, it has been removed as I was unable to find a top level comment (a direct reply to your post) from you in the post.\n\nYou have approximately 4 hours from the sending of this message to reply to your post with a comment that either includes a list the tweaks and themes used or where that list can be found. For example, if you included them in the imgur album description, you can simply write "Tweaks/themes used in album description".\n\nOnce you\'ve left a top level comment, **you need to reply to this PM to get your post approved.** When replying, please DO NOT change the subject of this message or send a new PM.\n\nIf you don\'t leave a top level comment and reply to this PM in the next 4 hours, you will be blocked from posting setups to /r/iOSthemes for 2 weeks (this is NOT the same as a ban from the subreddit).\n\nPlease see [this post](https://redd.it/5zsr0w) for more info.' + footer

def updateWiki():
	wp = r.subreddit(subreddit).wiki['setupbans']
	body = wp.content_md.splitlines()
	del body[0:4]
	banlist = []
	unbanIndex = []
	unbanUser = []

	for index, ban in enumerate(body):
		n, t = ban.split(' | ')
		if (float(t) < time.time()):
			print('  Unbanning /u/' + n)
			unbanIndex.append(index)
			unbanUser.append(n)
		else:
			print('  Add /u/' + n)
			banlist.append([n, t])

	for i in reversed(unbanIndex):
		del body[i]

	newPage = 'get UTC time in seconds and add 1,209,600: https://www.epochconverter.com/\r\n\r\nUsername | Ban End\r\n:--|:--'
	for ban in body:
		newPage += '\r\n' + ban

	if str(wp.content_md) != newPage:
		print('    editing the wiki page')
		reason = 'Unban'
		for user in unbanUser:
			reason += ' /u/' + user
		wp.edit(content = newPage, reason = reason)

	return banlist

def checkPosts(banlist):
	# Get the 50 newest posts in /r/iOSthemes
	for submission in r.subreddit(subreddit).new(limit = 15):
		print('  Checking post ' + submission.id + ' by ' + submission.author.name)

		for ban in banlist:
			if (submission.author.name == ban[0]) & (submission.link_flair_text == 'Setup'):
				print('    User is banned')
				submission.mod.remove()

				timeRemaining = float('%.2f'%((float(ban[1])-(time.time()))/(60*60*24)))
				unit = 'days'
				if timeRemaining < 1.0:
					timeRemaining *= 24
					unit = 'hours'

				submission.reply('Hello! Your setup post has been removed because you previously submitted a setup without including a theme/tweak list. You will be able to post setups again in ' + str(timeRemaining) + ' ' + unit + '.').mod.distinguish()

				break

		# Post needs to be older than 2 hours and less than 2.5, needs flair of Setup, and should not have been approved or removed by anyone
		if (2 <= (time.time()-submission.created_utc)/(60*60) < 2.25) & (submission.link_flair_text == 'Setup') & (submission.banned_by == None) & (submission.approved_by == None):
			print('    Checking [Setup]')
			# Look for a top level comment posted by the author
			authorReplied = False
			commentBody = ''
			for comment in list(submission.comments):
				if submission.author == comment.author:
					print('    TLC found!')
					authorReplied = True
					commentBody = comment.body
					break

			# The TLC is too short, so we report it for further review
			if (authorReplied) & (len(commentBody) < 100):
				submission.report(reason = 'OP\'s top level comment is short, please review')
			# The TLC is long enough, so approve it
			elif authorReplied:
				submission.mod.approve()
			# There is no TLC, so remove it
			else:
				if submission.is_self == False:
					print('    No TLC :(')
					submission.mod.remove()
					r.redditor(submission.author.name).message('Setup Post Removed - ' + submission.id, removalPM)
				else:
					submission.report(reason = 'Setup is a self post, please review')

		time.sleep(2)

def checkInbox():
	# Get the unread messages in the inbox
	for message in r.inbox.unread(limit = None):
		print('  Message from ' + message.author.name)

		# Make sure the message is a reply to one that SCB started
		if 're: Setup Post Removed - ' in message.subject:
			if ((time.time() - r.inbox.message(message.first_message_name[3:]).created_utc)/(60*60) > 4):
				response = 'Sorry, you took too long to reply to my PM and/or post a top level comment and your setup will not be approved.'
			else:
				print('    Looking for TLC')
				postID = message.subject[25:]
				post = r.submission(id = postID)
				# Look for a TLC from OP
				if post.id == postID:
					authorReplied = False
					for comment in list(post.comments):
						if message.author == comment.author:
							authorReplied = True
							commentBody = comment.body
							com = comment
							break

				# Approve post if reply was found
				if authorReplied:
					print('    Post approved!')
					post.mod.approve()
					response = 'Thanks! Your setup post has been approved.'
					if len(commentBody) < 100:
						com.report(reason = 'OP\'s top level comment is short, please review')
				# Ask them to try again if not
				else:
					print('    Nope :(')
					response = 'Sorry, I wasn\'t able to find a top level comment from you. Be sure that you are replying directly to your OWN POST, not to someone who replied to your post.'

			response += footer
			message.reply(response)
		elif (message.subject == 'username mention') & (message.author.name in mods):
			print('    Mention from /r/iOSthemes mod')
			post = r.submission(id=message.parent_id[3:])
			if post.link_flair_text == 'Setup':
				if message.body.lower() == '/u/setupcheckerbot remove':
					post.mod.remove()
					message.mod.remove()
					r.redditor(post.author.name).message('Setup Post Removed - ' + post.id, removalPM)
				elif message.body.lower() == '/u/setupcheckerbot ban':
					post.mod.remove()
					message.mod.remove()
					banUser(post.author.name)
		else:
			print('    Forward to admin')
			r.redditor(admin).message('FWD "' + message.subject + '" from /u/' + message.author.name, message.body)

		message.mark_read()
		time.sleep(2)

def checkSent():
	for message in r.inbox.sent(limit = 10):
		print('  PM to /u/' + message.dest.name)

		# Look for PMs to users, not to the admin
		if ('Setup Post Removed' in message.subject) & (message.dest.name is not admin):
			# If the PM is a "root" PM
			if (message.first_message == None) & (4 < (time.time() - message.created_utc)/(60*60) < 4.25):
				print('    Verifying TLC')
				verified = False
				# Check the replies to the root PM
				for m in list(r.inbox.message(message.id).replies):
					print('  Good')

					# If one of the replies is SCB approving a post, then we good
					if ('Thanks! Your setup post has been approved' in m.body) & (message.author == m.author):
						verified = True

				# Before banning, do one more check for a TLC
				if not verified:
					postID = message.subject[21:]
					post = r.submission(id = postID)
					if post.id == postID:
						for comment in list(post.comments):
							if message.dest == comment.author:
								post.mod.approve()
								verified = True

				# Ban if SCB didn't approve a post and if no TLC
				if not verified:
					banUser(message.dest.name)

		else:
			print('    Message to admin, skipping')

		time.sleep(2)

def banUser(author):
	wp = r.subreddit(subreddit).wiki['setupbans']
	if author in wp.content_md:
		print('  /u/' + author + ' is already banned')
	else:
		print('  Banning /u/' + author)
		banlength = 60*60*24*7*2
		body = wp.content_md + '\r\n' + author + ' | ' + str(time.time()+banlength)
		wp.edit(content = body, reason = 'Ban /u/' + author + ' for 2 weeks')

if __name__ == '__main__':
	r = praw.Reddit(client_id = clientid, client_secret = clientsecret, user_agent = userAgent, username = username, password = password)

	# Update the wiki
	print('Updating Wiki')
	banlist = updateWiki()

	# Review the setup posts
	print('Checking New Posts')
	checkPosts(banlist)

	# Check the inbox
	print('Checking Inbox')
	checkInbox()

	# Check sent messages
	print('Checking Sent Messages')
	checkSent()
