a = 5
b = 2
if a > b: print("a is greater than b")
#example2
a = 2
b = 330
print("A") if a > b else print("B")
#example3
a = 10
b = 20
bigger = a if a > b else b
print("Bigger is", bigger)
#example4
a = 330
b = 330
print("A") if a > b else print("=") if a == b else print("B")
#example5
x = 15
y = 20
max_value = x if x > y else y
print("Maximum value:", max_value)
#example6
username = ""
display_name = username if username else "Guest"
print("Welcome,", display_name)