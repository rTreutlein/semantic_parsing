
EXAMPLES = {
    "take one concept from the original sentencs and create a new sentence with it": [
        ("Animals eat Food", "Humans are Animals"),
        ("Animals eat Food", "Food is made from Animals/Plants"),
        ("Rain distributes water over land","Plants need water to grow")
    ]
}

EXAMPLES_OLD = {
        "consequence": [
            ("A plant that is watered regularly will grow.",
             "The growth of a plant will lead to the production of flowers or fruit."),
            ("Improving your physical fitness through daily exercise provides more energy and stamina.",
             "With increased energy and stamina, you are likely to perform daily tasks more efficiently."),
            ("Heavy rainfall results in wet streets.",
             "Wet streets can heighten the risk of slipping or traffic accidents."),
            ("Investing in the stock market can lead to financial gains or losses.",
             "Financial gains from investments may allow for increased speding on leisure activities."),
            ("Exposure of a book to the sun can cause its pages to yellow.",
             "Yellowing pages diminish the book's appearance and could reduce its value.")
        ],
        "precedence": [
            ("A plant that is watered regularly will grow.",
             "A plant must be in soil before it can be watered."),
            ("Improving your physical fitness through daily exercise provides more energy and stamina.",
             "One must start with light exercises before doing daily workouts."),
            ("Heavy rainfall results in wet streets.",
             "Clouds must form and gather before rainfall occurs."),
            ("Investing in the stock market can lead to financial gains or losses.",
             "One must open a brokerage account before investing in stocks."),
            ("Exposure of a book to the sun can cause its pages to yellow.",
             "A book must be placed near sunlight before it can be exposed.")
        ],
        "explanation": [
            ("A plant that is watered regularly will grow.",
             "Water helps plants to distribute nutrients"),
            ("Improving your physical fitness through daily exercise provides more energy and stamina.",
             "Exercise makes your heart stronger"),
            ("Heavy rainfall results in wet streets.",
             "Rain is water falling from clouds"),
            ("Investing in the stock market can lead to financial gains or losses.",
             "In the stocks market, investors buy and sell shares of companies"),
            ("Exposure of a book to the sun can cause its pages to yellow.",
             "Sunlight can fade the color of paper.")
        ],
        "contrast": [
            ("A plant that is watered regularly will grow.",
             "A plant may not grow if it is overwatered."),
            ("Improving your physical fitness through daily exercise provides more energy and stamina.",
             "Overdoing a single exercise may lead to fatigue."),
            ("Exposure of a book to the sun can cause its pages to yellow.",
             "Books kept in dark, cool places will not yellow.")
        ],
        "specialization": [
            ("A plant that is watered regularly will grow.",
             "A cactus requires only infrequent watering to grow."),
            ("Improving your physical fitness through daily exercise provides more energy and stamina.",
             "Engaging in cardio exercises, can specifically enhance lung capacity."),
            ("Heavy rainfall results in wet streets.",
             "Localized heavy rainfall can cause flash floods."),
            ("Exposure of a book to the sun can cause its pages to yellow.",
             "Acidic paper is more susceptible to yellowing.")
        ],
        "rephrasing": [
            ("A plant that is watered regularly will grow.",
             "Regular watering promotes the growth of plants."),
            ("Improving your physical fitness through daily exercise provides more energy and stamina.",
             "Daily exercise enhances physical fitness, leading to increased energy and endurance."),
            ("Heavy rainfall results in wet streets.",
             "Wet streets are a consequence of heavy rainfall."),
            ("Investing in the stock market can lead to financial gains or losses.",
             "The act of investing in stocks may result in either profit or loss."),
            ("Exposure of a book to the sun can cause its pages to yellow.",
             "Sunlight exposure can lead to the yellowing of a book's pages.")
        ]


    }
