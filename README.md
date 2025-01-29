# Multimodal Retrieval Project

Basic system of identifying ingredient images and then, ranking and retrieving recipes from MongoDB database.

Upload.py sets up a basic website, uploads images to google colab (CNN) to identify ingredients in the images, ranks recipes from MongoDB according to number of matched ingredients and displays the relevant results. 

AIR_model_training.ipynb contains the code of MobileNetV2 CNN training and hosting.

Intended Use: Novice cooks can identify ingredients by taking a picture and obtain recipes which can be made by the ingredients currently in hand. Recipes contain instructions to make Dishes.

Dataset used for training can be found here : https://drive.google.com/drive/folders/19lsyjJP0AAEps2O2zJdM7KYPYYfv-FSx?usp=sharing
