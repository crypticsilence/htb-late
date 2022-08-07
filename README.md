# htb-late
My scripts and write-up for the HackTheBox machine Late, an infuriating but rewarding box once it was cracked

I have decided to summarize this and remove my pages and pages of notes as I don't think they are very helpful in retrospect.  I've created a much longer writeup in htb-late.md. You're welcome. :)

Exploits can be found in the /imguploader directory.

:: Enumeration

The machine had a port 22 and 80 open, with a website titled 'Late - Best online image tools'. The page discussed image manipulation, and had a contact page that looked to not do anything..  Opened up the source to scan thru, and found a vhost in a link there, to 'http://images.late.htb'.  Added this to my /etc/hosts with the same IP and started scanning it with gobuster, and went and took a look at it.

This was a different and much simpler site. I was able to upload a jpg or png image, and convert it back into text, a process called OCR.   I tried this process through burp, saw if maybe I could upload different types of files, etc.  Nothing stood out to be too interesting, it only took images/* file types and only seemed to be happy with png or jpg files when I used burp intruder to try a few different file extensions.  It also mentioned at the top of the page that it used Flask, which really helped me find what I was looking for much quicker.  

:: Exploitation

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

:: Privesc

Root was *much* easier, found a script that runs after 3 bad ssh root logins to email the owner, called ssh-alert.sh.  I added a revshell oneliner to the bottom and forced 3 bad ssh logins to pop the rootshell.


## Interesting sidenote: 
2002 Holcombe Boulevard, Houston, TX 77030, USA is a veterans hospital

