# ex3
x = 0
while x <= 5.0:
    x = round(x, 1)
    if(x == 1.0):
        print(1)
    if(x == 2.0):
        print(2)
    if(x == 3.0):
        print(3)
    if(x == 4.0):
        print(4)
    if(x == 5.0):
        print(5)
    else:
        print(x)

    x += 0.1


# ex4
for i in range(1, 100):
    if(i % 10 == 7 or i-i % 10 == 70 or i % 7 == 0):
        print(i)

# ex5


def trim_whitespace(string_list):
    for i in range(len(string_list)):
        str = string_list[i]
        string_list[i] = str.rstrip()
    print(string_list)


# ex6
name = "Hello, my name is Inigo Montoya"
print(name[0:5])
print(name[7:14])
print(name[0::2])
print(name[2:19:2])

# ex7
num = int(input("Please enter a 5 digits number: "))
print(f"You entered the number: {num}")
print(
    f"The digits of this number are: {num//10000}, {num//1000%10}, {num//100%10}, {num//10%10}, {num%10}")
print(
    f"The sum of the digits is: {num//10000 + num//1000%10 + num//100%10 + num//10%10 + num%10}")

if __name__ == "__main__":
    trim_whitespace(["fewfwfe  ", "efw fewfew  "])
