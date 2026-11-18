from PIL import Image
src = r"C:\Users\54364\AppData\Local\Temp\qa-r38-f.png"
im = Image.open(src)
im.crop((1315, 495, 1600, 690)).resize((570, 390)).save(r"C:\Users\54364\AppData\Local\Temp\qa-r38-layers.png")
print("crop ok")
