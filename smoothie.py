import inflect


groceryList = {"strawberri": {
	"quantity": "5",
	"unit": "tablespoons",
	"ingredient": "strawberries"

}}

if __name__ == '__main__':
	info = groceryList["strawberri"]
	quantity = info["quantity"]
	print("quantity: " + quantity)
	info["quantity"] = str(float(quantity) + 2)
	print("new quantity: " + info["quantity"])
	print("new: " + groceryList["strawberri"]["quantity"])


