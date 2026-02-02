print(bool("Hello"))
print(bool(15))
#example2
x = "Hello"
y = 15

print(bool(x))
print(bool(y))
#example3
class myclass():
  def __len__(self):
    return 0

myobj = myclass()
print(bool(myobj))
#example4
def myFunction() :
  return True

print(myFunction())
#example5
def myFunction() :
  return True

if myFunction():
  print("YES!")
else:
  print("NO!")
  