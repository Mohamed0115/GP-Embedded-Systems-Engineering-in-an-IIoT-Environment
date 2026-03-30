def order ():
    X = input("choose \n 1.send \n 2.Return \n 3.Notify \n your answer: ")

    if X == 1:
        Z = input ("choose command \n"
                "1. Subscribe to Changes \n",
                "2. Unsubscribe to Changes \n",
                "3. Get Dynamic Sensors \n")
        if Z == 1:
            Y = {
                "Type": "GET_DYN",
                "From": "UI",
                "To": "SERV",
                "Data": {
                "Serials": []  # replace with your actual serial numbers
                },
            }


            return Y


    elif X == 2:
        Z = input ("choose command 1, 2, 3")

    elif X == 3:
        Z = input ("choose command 1, 2, 3")
    else :
        A = input("Enter your Command")

def main():
    order()


# we need to make two functions on for first choise and other for second one