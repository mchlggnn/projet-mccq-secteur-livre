from collections import defaultdict

class Book:
    def __init__(self, inDb1, inDb2, inDb3, inDb4, inDb5, isbn, lineNb):
        self.inDb1 = inDb1
        self.inDb2 = inDb2
        self.inDb3 = inDb3
        self.inDb4 = inDb4
        self.inDb5 = inDb5
        self.isbn = isbn
        self.number = lineNb





file = open("Alignement/alignement.csv", "r")

books = list()
lineNb = 0

for line in file.readlines():
    lineElements = line.split(", ")
    isbn = lineElements[0]
    inDb1 = len(lineElements[1]) > 0
    inDb2 = len(lineElements[2]) > 0
    inDb3 = len(lineElements[3]) > 0
    inDb4 = len(lineElements[4]) > 0
    inDb5 = len(lineElements[5]) > 0 and not lineElements[5] == "\n"
    book = Book(inDb1, inDb2, inDb3, inDb4, inDb5, isbn, lineNb)
    books.append(book)
    lineNb += 1

booksInDb1 = 0
booksInDb2 = 0
booksInDb3 = 0
booksInDb4 = 0
booksInDb5 = 0

booksInDb = defaultdict(int)

for book in books:
    numberDb = 0
    if book.inDb1:
        booksInDb1 += 1
        numberDb += 1
    if book.inDb2:
        booksInDb2 += 1
        numberDb += 1
    if book.inDb3:
        booksInDb3 +=1
        numberDb += 1
    if book.inDb4:
        booksInDb4 += 1
        numberDb += 1
    if book.inDb5:
        booksInDb5 += 1
        numberDb += 1
    
    booksInDb[numberDb] += 1
    if numberDb == 0 or numberDb == 1:
        print("Found book with only " + str(numberDb) + " occurrence, at line " + str(book.number) + " with ISBN " + str(book.isbn))

print("ADP : " + str(booksInDb1))
print("ILE : " + str(booksInDb2))
print("DL : " + str(booksInDb3))
print("Hurtubise : " + str(booksInDb4))
print("Babelio : " + str(booksInDb5))

print (booksInDb)