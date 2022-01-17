# -*- coding: utf-8 -*-
'''
Copyright (C) 2012-2018  Diego Torres Milano
Created on Jul 6, 2015

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

@author: Diego Torres Milano

'''
import json
import random

__author__ = 'diego'
__version__ = '20.5.1'

DEBUG = True


class Concertina:
    PHRASES = {
        "generic": [
            "Chicken Wings grow on trees",
            "Carrot sticks help the mind think",
            "Farts cause neurological damage",
            "Jennifer Lopez is a Man (only on Tuesday)",
            "That... Is what she said",
            "Make me a sandwich",
            "King Kong's brother was a Rabbit... Hmmm",
            "Tuesday, that's when it will all begin",
            "Rulers, do they rule the world?",
            "Can a pen write without writing it down.",
            "The iPod is a gigantic hummer",
            "A calculator can save the world. Just press \"On\"",
            "Cell phones... Do they have cells in them?",
            "A battery can produce random flashes and generate helium. Doubtful",
            "A flash drive produces no flash what so ever",
            "A card can be a type of a pickle, if its a pickle card",
            "just a minute",
            "wait for me",
            "it was silent",
            "chaos reigned",
            "be on time",
            "get away from me",
            "Hold that thought",
            "settle down",
            "by the light of the street lamp",
            "slippers soaked from the heavy dew",
            "haunted by the oddly familiar musid",
            "The 'poke' button on facebook is awesome...\\\nBut I think there should be a 'stab' button...",
            #
            # Was riding a horse yesterday and fell off. I almost got killed! THANK GOODNESS
            # the Walmart greeter saw what happened and came over and unplugged it.
            #
            # Ayone who says "nothing is impossible" has obviously never  tried to staple jello to a tree.
            #
            # Text someone and tell them "Hey, I lost my phone, can you call it?"  and see how many people call it
            #
            # Bottles of bleach: $15.00. One rope, 3 rolls of duct tape, and a shovel: $35.00. 3 boxes of trash bags: $10.00. The look on the cashier's face: Priceless!
            #
            # Don't you hate it when you're texting and laying on your back and  your phone decides to be a ninja, slips through your fingers, and attacks your face!
            #
            # Robin Hood was a thief, Mario gets high off of Mushrooms, Snow White lived with 7 men,  Sleeping Beauty always slept in, and our parents wonder why WE are bad!
            #
            # In my will, I'm giving $50 to anyone who wears a Grim Reaper costume to my funeral and doesn't say a word
            #
            # "You know you're too drunk to drive when you swerve to miss a tree,  and then realize it was just your air freshener hanging from the rear view mirror."
            #
            # Dares you to go outside, throw a rock at your car and yell  "like a good neighbor statefarm is there!"
            #
            # My doctor asked if any members of my family suffered from insanity, I replied, no, we all seem to enjoy it
            #
            # Pshhhh I did not fall... The floor looked at me funny so I used my mad ninja skills to attack
            #
            # My new word for the day is FOCUS, when someone irritates you tell them 2 FOCUS (F*** Off Cuz Ur Stupid)
            #
            # Just remember, everything happens for a reason. So when I smack you upside the head, remember... I had a reason!
            #
            # Have you ever started laughing for no reason, then started laughing even harder because you were laughing for no reason? I Love those moments.
            #
            # Today I went on thesaurus.com and searched "ninjas". The computer told me "ninjas cannot be found"  Well played, ninjas, well played
            #
            # What the voices in my head tell me to do would get me arrested in all 50 states and 26 countries
            #
            # Stalking is such a strong word  ~ I prefer to think of it more as 'intense research' on one individual  ~ By the way, your missing sock is under your bed, with me
            #
            # I think my guardian angel is bipolar
            #
            # WARNING: I have officially been left unsupervised.  I take no responsibility for what may happen in the next few hours.
            #
            # I didn't trip, I... I was... uh... just... uh... checking the gravity!
            # Yeah! Just so you know, it's all good, it still works.
            #
            # I dare someone to kidnap me as soon as my meds wear off..they'll pay me to leave!
            #
            # I wonder if its bad when I'm talking to myself and I'm not even listening
            #
            #  I'm going out to look for myself, if you see me before i return, please tell myself to call me so i know where i am.
            #
            # I know what your doing,I'm watching u do this, if your wondering what your doing i would know,wanna know what your doing?  you reading my status you stalker!
            #
            # This year I'm using big words to sound smart...  Sorry, I meant utilizing gargantuan idioms to simulate intelligence.
            #
            # Y'know those signs you see in towns that say,  "Drive careful, we love our children".  DUH, you're not gonna see a sign that says, "GUN IT, WE'LL MAKE MORE!"
            #
            # No officer, I did not hit her, I simply Fist Pumped her face!
            #
            # I like throwing Skittles at people and shouting TASTE THE RAINBOW!!  but it's more fun to throw tacos at people yelling '  THINK OUTSIDE THE BUN!!
            #
            # I love to stand in line at ATM machines, and when people put in their PIN, I yell GOT IT then run away
            #
            # Like a weird neighbor, stalkers are there!
            #
            # Some people were dropped as a baby
            # . YOU were clearly thrown at a wall. Then feed a bottle of wacko-o juice!
            #
            # Do you ever find yourself really bored so you go on Facebook
            # yet you find that there is nothing to do except refresh the page until something new pops up?
            #
            # OK think of a number. Add 12 to the number. Subtract 2. Divide that number by 5. Add 20. Did you get 12? Neither did I.
            # I just wanted to see if you would do it!
            #
            #  im going to get a job at walmart as a greeter
            # and my words of welcome will be "Welcome to freaking walmart! Get ur sh*t and get the hell out!!"
            #
            # Brunette:When I grow up, I'LL GO TO MARS.
            # Blondie:When I grow up I'LL GO TO THE SUN.
            # Brunette:But you will burn!
            # Blondie:Don't be stupid, I'll go at night
            #
            # If somebody throws skittles at me and yells "TASTE THE RAINBOW",
            # I'm gonna throw a 2 liter bottle of Dr.Pepper and yell "TRUST ME I'M THE DOCTOR
            #
            # a few days ago I very sternly told the voices in my head to stop talking to me.
            # Now they are sending me txt mgs say that they r sorry and want to get back2gethr
            #
            # things to do at Walmart: hide behind teddy bears and make evil laughing noises when little kids come by
            #
            # Ever feel like beating someone with a baseball bat to the point of almost unconsciousness, then setting them on fire? No? Just me?
            #
            #  I'm not crazy.. don't you judge me! Your just jealous cause i get texts from the flying gummy bears and you don't!
            #
            # i saw a flying cow yesterday. it was purple and i named him Phillip...i wish the dancing unicorn had seen him but she was too busy laughing at Steve the snake
            #
            #  i was sitting there when i got attacked by the purple hedgehogs, neon dragons, and glow-in-the-dark leprechauns that kid-napped the unicorn and strawberry king
            #
            # I have decided to stop pretending and just be that ninja with the magical penguins and dinosaurs and unicorns that everyone KNOWS I am.
            #
            # Have you ever tried walking into Walmart and yelling red robin! and seeing how many people say YUM red robin, red robin, come on just say yum!
            #
            #  Things to do at Walmart #365: bring or take a tent, set it up in a camping supplies corner, and camp out for the weekend until they kick you out!
            #
            # After watching CSI, Cold case, Law & Order, and all those other educational shows, I'm 99% sure I can make sure nobody notices you missing. Just saying...
            #
            # I like to call it doing the world a favor. Homicide is just the technical term
            #
            #  i think there's something wrong with my guardian angel.
            # her wings are black and she's sitting with the devil and laughing hysterically at everything and everyone
            #
            # I got a special care pkg. in the mail. It had duct tape, a meat tenderizer,
            # a hole punch and a note saying " don't get caught"! (sigh) I love my friends!
            #
            # I find myself meeting people who give me the honor of thinking up new words... Dipshidiot! (dip-shid-iot)
            #
            # backwards this read you making am i why exactly is that, never? you to nice been ever I have when since (now read it backwards)
            #
            # What happens in an exam : Tik tok , Mind block , Pen stop , Eye pop , Full shock , Jaw drop , Time up , No Luck
            #
            #  O I dare you to walk up to any officer and say:
            # I didnt do it I didnt kill her, the assassination wasnt part of the plan.' Then run fast! I bet they'll chase u
            #
            # I'm bored & in need of some adventure. I say we get drunk, get stupid, get a stick, go poke something with teeth and see if we can outrun it.
            #
            # Why do people always think my friends and I are high? WE'RE NOT ON DRUGS! We're just crazy, and loud, and random, and scooby doo (but that's a different story)
            #
            #  Smile people will wonder what your up to.But grin like crazy and they will want to know what the hell you just did
            #
            # Isn't it funny how everyone thinks they are the normal one in their family?
            #
            # For Sale! One used alarm clock. damn thing rings when I am trying to sleep.
            #
            #  im on my way to Walmart to take the "try me" stickers off the noise making toys and stick them on condom boxes.

        ],
        "alexa": [
            "Alexa, E.T. phone home",
            "Alexa, tell me a wizard joke",
            "Alexa, what's up?",
            "Alexa, what can you do?",
            "Alexa, show me restaurants in Montreal",
            "Alexa, what’s the news?",
            "Alexa, why is Pluto not a planet?",
            "Alexa, translate ’good morning’ in Japanese.",
            "Alexa, open TuneIn Live.",
            "Alexa, what’s your favorite word?",
            "Alexa, who’s leading the Masters?",
            "Alexa, play 'Your Song' by Lady Gaga.",
            "Alexa, set a sleep timer for ten minutes.",
            "Alexa, who is your favorite poet?",
            "Alexa, tell me a baseball joke.",
            "Alexa, read my audiobook.",
            "Alexa, teach me something.",
            "Alexa, why is water wet?",
            "Alexa, how do I set up calling and messaging?",
            "Alexa, give me a tongue twister.",
        ]
    }

    EMAILS = [
        "user@example.com",
        "user@gmail.com",
        "user@yahoo.com",
        "user@outlook.com",
        "user@mail.com",
        "user@outlook.co.uk",
    ]

    PASSWORDS = [
        "123456",
        "password",
        "12345678",
        "qwerty",
        "abc123",
    ]

    PLACES = [
        "los angeles",
        "seattle",
        "ushuaia",
        "white horse",
        "berlin"
    ]

    def __init__(self):
        pass

    @staticmethod
    def getRandomText(target=None):
        if target is None:
            target = 'generic'

        return random.choice(Concertina.PHRASES[target])

    @staticmethod
    def sayRandomText(target=None):
        return Concertina.getRandomText(target)

    @staticmethod
    def getRandomEmail():
        return random.choice(Concertina.EMAILS)

    @staticmethod
    def getRandomPassword():
        return random.choice(Concertina.PASSWORDS)

    @staticmethod
    def getRandomPlace():
        return random.choice(Concertina.PLACES)

    @staticmethod
    def readConcertinaConfig(concertinaConfigFile):
        if concertinaConfigFile:
            config = json.load(open(concertinaConfigFile))
        else:
            config = dict()
        if 'limits' not in config:
            config['limits'] = dict()
            config['limits']['iterations'] = 100
            config['limits']['maxNoTargetViewsIterations'] = 25
        if 'probabilities' not in config:
            config['probabilities'] = dict()
            config['probabilities']['systemKeys'] = 1 / 6.0
            config['probabilities']['views'] = 5 / 6.0
        if 'systemKeys' not in config:
            config['systemKeys'] = dict()
            config['systemKeys']['keys'] = ['ENTER', 'BACK', 'HOME', 'MENU']
            n = float(len(config['systemKeys']['keys']))
            config['systemKeys']['probabilities'] = [1 / n for _ in config['systemKeys']['keys']]
        if 'views' not in config:
            config['views'] = dict()
            config['views']['selector'] = ['classes', 'contentDescriptions']
            config['views']['probabilities'] = [0.5, 0.5]

            config['views']['classes'] = dict()
            config['views']['classes']['regexs'] = ['android.widget.Button', 'android.widget.EditText',
                                                    'android.widget.Scrollable', '.*']
            n = float(len(config['views']['classes']['regexs']))
            config['views']['classes']['probabilities'] = [1 / n for _ in config['views']['classes']['regexs']]

            config['views']['contentDescriptions'] = dict()
            config['views']['contentDescriptions']['regexs'] = ['.*']
            n = float(len(config['views']['contentDescriptions']['regexs']))
            config['views']['contentDescriptions']['probabilities'] = [1 / n for _ in
                                                                       config['views']['contentDescriptions']['regexs']]

        return config

    @staticmethod
    def getConcertinaConfigDefault():
        return json.dumps(Concertina.readConcertinaConfig(None), indent=4, sort_keys=True)
