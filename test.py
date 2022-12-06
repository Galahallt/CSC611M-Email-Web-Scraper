import multiprocessing

if __name__ == "__main__":
    final_personnel = multiprocessing.Queue()

    personnel_info = dict()

    personnel_info["fullname"] = "Paolo Espiritu"
    personnel_info["email"] = "espiritu.paolo1@gmail.com"
    personnel_info["department"] = "CCS"

    final_personnel.put(personnel_info)

    for a, v in final_personnel.get().items():
        print(v)

    # with open("test.txt", "w") as file:
    #     file.write("Full Name,Email,College\n")
    #     while not final_personnel.empty():
    #         file.write(",".join([str(a) for a in final_personnel.get()]) + "\n")
