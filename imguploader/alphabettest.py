from PIL import Image, ImageDraw, ImageFont
import os
import requests
import argparse

# This was file 2/3 .. Created to test the alphabet using each font found in different sizes against the tesseract engine and see how accurate
# the resulting string was.

# url of the ImageReader page we are attacking
#url = "http://127.0.0.1:5000/scanner"
url = "http://images.late.htb/scanner"
# prefix of the img files to save
pre="test_"
# ext of the img files
ext=".png"
# Font files to use for the image are now figured out dynamically below
fontfiles=[]
# Font size to start with
fontsize=12
# Last font size to test
maxfontsize=34
# Save images? 0=no 1=yes
imgsave=1
# image number to start with (if you are saving the images)
num=0
hit=[]
highscore=0
highfontfile=""
highfontsize=0

def send(fname,num,txt):
    chnum=0
    likeness=0
    #print("[.] sending file "+fname+" to "+url+" ..",)
    #print("from: "+txt+" len: "+str(len(txt)))
    file = {'file': open(fname, 'rb')}
    r=requests.post(url, files=file)
    code=str(r.status_code)
    resp=r.text.replace("\r\n","").replace("<p>","").replace("</p>","")
    for ch in resp:
        if chnum<len(txt):
            # resp might be longer, and usually is..
            #print("compare: "+txt[chnum]+" to "+ch)
            if ch == txt[chnum]:
                # problem = one space early on and likeness is screwed, could be inaccurate, but most are towards the end..
                likeness+=1
        chnum+=1
    numscore=round((likeness/len(txt))*100)
    score=str(numscore)
    print(code+" "+score+"%\t"+resp)
    if (len(r.text)>120):
        hit+=num
        print("[!] "+num+" = Likely hit, >120chars")
    return(numscore)

print("\n\n")
print("imguploader.py - crypticsilence 2022-05-07")
print("  made for htb box lame.htb")
print("  creates a .png file with text using PIL ImageDraw.Draw(), and uploads to a site via POST")
print("  you should test with an alphabettest.py first, and make sure your font is returning the correct reply text!")
print("  Score is a percentage that will show the results of the current font w/ tesseract..")
print("\n\n")
print("Code Score String")

x=0
print("Font files found : ")
for file in os.listdir("."):
    if file.endswith(".ttf"):
        print("x:"+str(x)+" file:"+file)
        fontfiles+=[file]
        x+=1

while fontsize<maxfontsize:
    for fontfile in fontfiles:
        print("Trying font file "+fontfile+" size: "+str(fontsize))
        try:
            fnt = ImageFont.truetype(fontfile,fontsize)
        except:
            print("[X] ERROR: Couldn't load font!!")
            break
        txt="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`0123456789~!@#$%^&*()_+[]\\{}|;':\",./<>?"
        # create new image for each ssti attempt- which must be a single line!
        print("Tried:\t"+txt.strip("\n"))
        try:
            image = Image.new(mode = "RGB", size = (2600,80), color = "black")
            draw = ImageDraw.Draw(image)
            draw.text((10,10), txt, font=fnt, fill=(255,255,255))
            filename = pre+str(num)+ext
        except:
            print("[X] Error: error drawing text...")
            break
        try:
            image.save(filename)
        except:
            print("[X] Error: error saving file...")
            break
        try:
            score=send(filename,num,txt)
        except:
            print("[X] Error: caught error sending...")
            break
        if score>highscore:
            highscore=score
            highfontfile=fontfile
            highfontsize=fontsize
            if highscore==100:
                # might as well quit, we got it ;>
                break
        num+=1
    fontsize+=1

print("Winning font/size:")
print("  "+str(highscore)+" "+highfontfile+" "+str(highfontsize)+" pts")

if not imgsave:
    os.system("rm "+pre+"*.png")
else:
    print("[o] Saved "+str(num)+" png images")
