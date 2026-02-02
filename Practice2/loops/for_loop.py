fruits = ["apple", "banana", "cherry"]
for x in fruits:
  print(x)
#example2
for x in "banana":
  print(x)
#example3
for x in range(6):
  if x == 3: break
  print(x)
else:
  print("Finally finished!")
#example4
for x in range(6):
  print(x)
else:
  print("Finally finished!")
#example5
for x in range(2, 30, 3):
  print(x)
#example6
for x in range(6):
  print(x)
#example7
adj = ["red", "big", "tasty"]
fruits = ["apple", "banana", "cherry"]

for x in adj:
  for y in fruits:
    print(x, y)