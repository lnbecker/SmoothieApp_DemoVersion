from flask import Flask, render_template, request
import json
import nltk
from nltk.corpus import wordnet as wn
import json
import random
from nltk.stem.snowball import SnowballStemmer
from nltk.stem.porter import PorterStemmer
import inflect
from fractions import Fraction

groceryDict = {}

app = Flask(__name__)

@app.route('/')
def output():
	# serve index template
	return render_template('index.html', name='Smoothie')

@app.route('/recipeAdded', methods=['POST'])
def addRecipe():
	# sends "1 1/2 cups watermelon, 2 apples, 3 inches fresh ginger"
	dataString = request.form.get('data')
	data = dataString.split(",")
	#return json.dumps(data)
	for sentence in data:
		#Parse line
		wordDict = parseLine(sentence)

		if wordDict:
			quantity = wordDict["quantity"]
			ingredient = wordDict["ingredient"]
			stem = snowballStem(ingredient)

			if 'unit' in wordDict.keys():
				unit = wordDict["unit"]

			if stem in groceryDict:
				print("stem " + stem + " is in groceryDict")
				info = groceryDict[stem]
				oldQuantity = convertToFloat(info["quantity"])
				if 'unit' in wordDict.keys():
					oldUnit = info["unit"]
				oldIngredient = info["ingredient"]
				info["quantity"] = str(Fraction((float(oldQuantity) + float(quantity))))
				#Check if units are the same
				if 'unit' in wordDict.keys():
					if (oldUnit != unit):
						if (isSingular(oldUnit)):
							print("singular \n")
							newUnit = pluralize(oldUnit)
							#if (newUnit != unit):
							#Units are totally different (one is not just plural form) - For now, do nothing but edit this eventually
							info["unit"] = newUnit
					if ((oldUnit == unit) & isSingular(unit)):
						info["unit"]=pluralize(unit)
					# else units are the same so no need to change
				else:
					info["unit"] = ""
				#Make sure ingredient is plural now
				if(isSingular(oldIngredient)):
					if(isSingular(ingredient)):
						newIngredient = pluralize(ingredient)
						info["ingredient"] = newIngredient
					else: #ingredient is already plural
						info["ingredient"] = ingredient
				# else ingredient is already plural, we don't need to change
			else:
				#ingredient is not already in wordDict, add it
				if 'unit' not in wordDict.keys():
					unit = ""
					print("no unit")
				groceryDict[stem] = {"quantity": str(Fraction(quantity)), "unit": unit, "ingredient" : ingredient}

	#return json you want JS to have
	return json.dumps(groceryDict)



###########################     INGREDIENT PARSER       ###########################

ingredientsList = []
quantitiesList = []
unitsList = []
global classifier

def pos_features(word):
	arrayForm = []
	arrayForm.append(word)
	a, b = nltk.pos_tag(arrayForm)[0]
	return {"POS" : b}

#food list
food = wn.synset('food.n.02')
ingredientsList = list(set([w for s in food.closure(lambda s:s.hyponyms()) for w in s.lemma_names()]))

#quantity list
numList = []
fractions = ["1/8", "1/4", "1/3", "1/2", "2/3"]
wholeNums = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
for whole in wholeNums:
	for frac in fractions:
		numList.append(whole + " " + frac)
quantitiesList = numList + wholeNums + fractions

#unit list
unitsList = ["teaspoon", "teaspoons", "tablespoon", "tablespoons", "handful", "handfuls", "whole", "cup", "cups", "stick", "sticks", "packet", "packets", "oz", "ounces", "pound", "pounds", "lb", "lbs", "fluid ounces", "fluid ounce", "pint", "pints", "quart", "quarts", "gallons", "gallon", "fluid oz.", "fluid oz", "oz.", "ml", "millileters", "liter", "liters", "inch", "inches", "in", "centimeters", "cm", "centimeter", "stalks", "stalk"]

labeled_words = ([(word, 'ingredient') for word in ingredientsList] + [(word, 'unit') for word in unitsList] + [(word, 'quantity') for word in quantitiesList])
random.shuffle(labeled_words)
featuresets = [(pos_features(word), type) for (word, type) in labeled_words]
train_set, test_set = featuresets[500:], featuresets[:500]
classifier = nltk.NaiveBayesClassifier.train(train_set)


def classifyWord(word):

	if word in ingredientsList:
		return "ingredient"
	if word in quantitiesList:
		return "quantity"
	if word in unitsList:
		return "unit"
	else:
		return classifier.classify(pos_features(word))

def convertToFloat(frac_str):
    try:
        return float(frac_str)
    except ValueError:
        num, denom = frac_str.split('/')
        try:
            leading, num = num.split(' ')
            whole = float(leading)
        except ValueError:
            whole = 0
        frac = float(num) / float(denom)
        return whole - frac if whole < 0 else whole + frac

def parseLine(sentence):
	wordArray = nltk.word_tokenize(sentence)
	wordDict = {}
	
	# For cases where ingredient or quantities are two words
	previousTag = ""
	previousWord = ""

	for word in wordArray:
		tag = classifyWord(word)
		#print("word: " + word + " tag: " + tag)
		if (tag == previousTag):
			word = previousWord + " " + word
		if (tag=="quantity"):
			wordDict["quantity"] = str(convertToFloat(word))
		if(tag == "unit"):
			wordDict["unit"] = word
		if(tag == "ingredient"):
			wordDict["ingredient"] = word

		previousTag = tag
		previousWord = word
	return wordDict


#Makes singular if plural, makes plural if singular
def pluralize(word):
	engine = inflect.engine()
	return engine.plural(word)

def isSingular(word):
	engine = inflect.engine()
	return engine.singular_noun(word) == False

def sameStem(word1, word2):
	return ((snowballStem(word1) == snowballStem(word2)) or porterStem(word1) == porterStem(word2))

#Two stemming algorithms
def snowballStem(word):
	stemmer = SnowballStemmer("english")
	return stemmer.stem(word)
def porterStem(word):
	porter_stemmer = PorterStemmer()
	return(porter_stemmer.stem(word))

if __name__ == '__main__':
	app.debug = True
	app.run()

   


			