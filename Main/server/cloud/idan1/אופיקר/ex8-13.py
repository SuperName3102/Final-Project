# ex8
import math


def my_sum(lst):
    total = lst[0]  # משתנה לאחסון החיבור הסופי

    for item in lst:
        if(item == lst[0]):
            continue
        total += item  # הוספת האיבר לסכום

    return total


# ex9 A
def donuts(count):
    if(count >= 10):
        return "many"
    else:
        return count

# B


def both_ends(s):
    if(len(s) < 2):
        return ""
    else:
        return(s[0:2]+s[-2:len(s)])


# C
def fix_start(s):
    fl = s[0]
    return(fl+s[1:].replace(fl, "*"))

# D


def mix_up(a, b):
    return(b[0:2]+a[2:]+" "+a[0:2]+b[2:])


def test(got, expected):
    if got == expected:
        prefix = ' OK '
    else:
        prefix = '  X '
    print(f'{prefix} got: {repr(got)} expected: {repr(expected)}')


# ex9 D
def verbing(s):
    if(len(s) < 3):
        return s
    elif(s[-3:] == "ing"):
        return (s+"ly")
    else:
        return (s+"ing")

# E


def not_bad(s):
    index_not = s.find('not')
    index_bad = s.find('bad')

    if index_not != -1 and index_bad != -1 and index_bad > index_not:
        return s[:index_not] + 'good' + s[index_bad + 3:]
    else:
        return s


# F


def front_back(a, b):
    if(len(a) % 2 == 0):
        a_front = a[0:len(a)//2]
        a_back = a[len(a)//2:]
    else:
        a_front = a[0:len(a)//2+1]
        a_back = a[len(a)//2+1:]

    if(len(b) % 2 == 0):
        b_front = b[0:len(b)//2]
        b_back = b[len(b)//2:]
    else:
        b_front = b[0:len(b)//2+1]
        b_back = b[len(b)//2+1:]
    return (a_front + b_front + a_back + b_back)


# ex11 A
def match_ends(list):
    counter = 0
    for item in list:
        if(len(item) < 2):
            continue
        if(item[0:1] == item[-1:]):
            counter += 1
    return counter

# B


def front_x(list):
    x_starting = []
    other_strings = []

    for string in list:
        if string.startswith('x'):
            x_starting.append(string)
        else:
            other_strings.append(string)

    x_starting.sort()
    other_strings.sort()
    sorted_strings = x_starting + other_strings

    return sorted_strings

# C


def sort_last(tuples):
    sorted_tuples = sorted(tuples, key=lambda x: x[-1])
    return sorted_tuples


# ex12 D
def remove_adjacent(nums):
    if not nums:
        return []

    result = [nums[0]]

    for num in nums[1:]:
        if num != result[-1]:
            result.append(num)

    return result

# E


def linear_merge(list1, list2):
    merged_list = []
    i, j = 0, 0

    while i < len(list1) and j < len(list2):
        if list1[i] < list2[j]:
            merged_list.append(list1[i])
            i += 1
        else:
            merged_list.append(list2[j])
            j += 1

    merged_list.extend(list1[i:])
    merged_list.extend(list2[j:])

    return merged_list


# ex13


def circle_area(radius):
    return math.pi * radius*radius


def triangle_area(ray1, ray2, angle):
    return ray1*ray2*math.sin(angle)/2


def angle(m1, n1, m2, n2):
    return math.degrees(math.atan(abs((m1-m2)/(1+m1*m2))))


def main():
    print('donuts')
    # Each line calls donuts, compares its result to the expected for that call.
    test(donuts(4), 'Number of donuts: 4')
    test(donuts(9), 'Number of donuts: 9')
    test(donuts(10), 'Number of donuts: many')
    test(donuts(99), 'Number of donuts: many')

    print()
    print('both_ends')
    test(both_ends('spring'), 'spng')
    test(both_ends('Hello'), 'Helo')
    test(both_ends('a'), '')
    test(both_ends('xyz'), 'xyyz')

    print()
    print('fix_start')
    test(fix_start('babble'), 'ba**le')
    test(fix_start('aardvark'), 'a*rdv*rk')
    test(fix_start('google'), 'goo*le')
    test(fix_start('donut'), 'donut')

    print()
    print('mix_up')
    test(mix_up('mix', 'pod'), 'pox mid')
    test(mix_up('dog', 'dinner'), 'dig donner')
    test(mix_up('gnash', 'sport'), 'spash gnort')
    test(mix_up('pezzy', 'firm'), 'fizzy perm')

    print('verbing')
    test(verbing('hail'), 'hailing')
    test(verbing('swiming'), 'swimingly')
    test(verbing('do'), 'do')

    print()
    print('not_bad')
    test(not_bad('This movie is not so bad'), 'This movie is good')
    test(not_bad('This dinner is not that bad!'), 'This dinner is good!')
    test(not_bad('This tea is not hot'), 'This tea is not hot')
    test(not_bad("It's bad yet not"), "It's bad yet not")

    print()
    print('front_back')
    test(front_back('abcd', 'xy'), 'abxcdy')
    test(front_back('abcde', 'xyz'), 'abcxydez')
    test(front_back('Kitten', 'Donut'), 'KitDontenut')

    print
    ('match_ends')
    test(match_ends(['aba', 'xyz', 'aa', 'x', 'bbb']), 3)
    test(match_ends(['', 'x', 'xy', 'xyx', 'xx']), 2)
    test(match_ends(['aaa', 'be', 'abc', 'hello']), 1)

    print()
    print('front_x')
    test(front_x(['bbb', 'ccc', 'axx', 'xzz', 'xaa']),
         ['xaa', 'xzz', 'axx', 'bbb', 'ccc'])
    test(front_x(['ccc', 'bbb', 'aaa', 'xcc', 'xaa']),
         ['xaa', 'xcc', 'aaa', 'bbb', 'ccc'])
    test(front_x(['mix', 'xyz', 'apple', 'xanadu', 'aardvark']),
         ['xanadu', 'xyz', 'aardvark', 'apple', 'mix'])

    print()
    print('sort_last')
    test(sort_last([(1, 3), (3, 2), (2, 1)]),
         [(2, 1), (3, 2), (1, 3)])
    test(sort_last([(2, 3), (1, 2), (3, 1)]),
         [(3, 1), (1, 2), (2, 3)])
    test(sort_last([(1, 7), (1, 3), (3, 4, 5), (2, 2)]),
         [(2, 2), (1, 3), (3, 4, 5), (1, 7)])
    print('remove_adjacent')
    test(remove_adjacent([1, 2, 2, 3]), [1, 2, 3])
    test(remove_adjacent([2, 2, 3, 3, 3]), [2, 3])
    test(remove_adjacent([]), [])

    print()
    print('linear_merge')
    test(linear_merge(['aa', 'xx', 'zz'], ['bb', 'cc']),
         ['aa', 'bb', 'cc', 'xx', 'zz'])
    test(linear_merge(['aa', 'xx'], ['bb', 'cc', 'zz']),
         ['aa', 'bb', 'cc', 'xx', 'zz'])
    test(linear_merge(['aa', 'aa'], ['aa', 'bb', 'bb']),
         ['aa', 'aa', 'aa', 'bb', 'bb'])

    print(angle(1, 10, 0.5, 50))


if __name__ == '__main__':
    main()
