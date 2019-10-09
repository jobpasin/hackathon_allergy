# Tokyo Junction Hackathon 2019: Allergy detection application 
Prototype of application created in Tokyo Hackathon 2019. 

For an upcoming Olympics 2020, a lot of foreigners will come to Japan and some of them might have some allergies 
but they are not sure if the food product they found has those ingredients or not since it is in Japanese. 
<br> Our goal is for these tourist who cannot read Japnaese to be able to check allergies by taking picture on any food label.

This code is only for the text detection algorithm part which I am responsible for. This does not include backend and frontend 
to application part in this repo.

This application is supported by [Rakuten API](https://api.rakuten.co.jp/en/) which gives various ML services for fast prototyping.


## Algorithm

Here is an overview of how our application works. Note that since this is a 48 hours competition, we focus on doing more simple algorithm first.

1. Use OCR to retrieve all text in any given image. (In Japanese as a default)

2. Check if any text is the same as our dictionary of allergy words. We check [27 most common ingredients](https://farrp.unl.edu/77c3494f-6568-42f3-b62c-f97d21eb2586.pdf) 
from Consumer Affairs Agency, Government of Japan as initial list of allergies. 

3. In order to cross-check the accuracy, we translate the whole text detected from Japanese to English using text translation 
by two diffrent services and check if the same allergy (in English) also exist in the translation

4. When found any allergy which exist in both Japanese and the traslated English, send the output to frontend


## Challenges

- False negative is what really important in our case so we need to double-check to ensure there is no allergy in the image. 
On the other hand, double-checking also increase processing time as well because it takes some time for API services to give us the result

- OCR cannot detect every character and sometimes the ingredients name is in Kanji/Hiragana/Katagana unlike English word 
so we have to check all possible name.


