from PIL import Image
im=Image.open(r"C:\Users\54364\AppData\Local\Temp\rec43_v.png")
im.crop((300,120,820,880)).save(r"C:\Users\54364\AppData\Local\Temp\rec43_preview.png")
print("crop ok")
