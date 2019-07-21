# -*- coding: utf-8 -*-
import unirest
import ssl
import jaconv


# Get information from image using Microsoft CV API
def ocr(url_link):
    # print("{\"url\":\"%s\"}" % url_link)
    response = unirest.post("https://microsoft-azure-microsoft-computer-vision-v1.p.rapidapi.com/ocr?language=unk",
                            headers={
                                "",  # Add api-key here,
                                "Content-Type": "application/json"
                            },
                            params=("{\"url\":\"%s\"}" % url_link)
                            )
    ocr_words = []
    result = response.body
    # If not detect any text, return 'unk' language
    try:
        region_word = list()
        region_word_bb = list()
        language = result[u'language']
        for region in result[u'regions']:
            for line in region[u'lines']:
                sentence = ''
                for word in line[u'words']:
                    region_word.append(word[u'text'])
                    region_word_bb.append(word[u'boundingBox'])
                    # print(word[u'text'])
                    sentence = sentence + word[u'text']
        result_region = {'word': region_word, 'bb': region_word_bb}
        ocr_words.append(result_region)
        # print("Full sentence : " + word_list_to_str(all_word) + "\n")
    except KeyError:
        # print(result)
        # print(url_link)
        try:
            print("OCR Error: %s" % result[u'message'])
        except KeyError:
            print("OCR Error: Unknown reason")
        all_word = []
        all_word_bb = []
        language = 'unk'
    print("Number of regions: %s" % len(ocr_words))
    return ocr_words, language


# Check if the "ingredient" word exist, if 3 or more exist
def check_keyword(keywords, ocr_word):
    count = 0
    for d in keywords:
        for c in ocr_word['word']:
            if d == c:
                count = count + 1
                break
    if count >= 2:
        return True
    else:
        return False


# Keep only dictionary which their values exist in filter_words
def filter_values(dict_words, filter_words):
    if filter_words is None:
        return dict_words
    new_dict = {}
    for key, values in dict_words.iteritems():
        for value in values:
            if value in filter_words:
                new_dict[key] = values
                break
    return new_dict


# Using freemium microsoft text translation
def translate_microsoft(text, language="en"):
    url = "https://microsoft-azure-translation-v1.p.rapidapi.com/translate?to=%s&text=%s" % (language, text)
    url = url.encode('utf-8')
    response = unirest.get(url,
                           headers={
                               ""  # Add api-key here
                           }
                           )
    full_response = response.body
    translation = full_response.replace("<string xmlns=\"http://schemas.microsoft.com/2003/10/Serialization/\">",
                                        "").replace("</string>", "")
    return translation


# Using Free SYSTRAN.io for optional text translation
def translate_sys(text, language="en"):
    url = "https://systran-systran-platform-for-language-processing-v1.p.rapidapi.com/translation/text/translate?source=auto&target=%s&input=%s" % (
        language, text)
    url = url.encode('utf-8')
    # print(url)
    try:
        response = unirest.get(url,
                               headers={
                                   ""  # Add api-key here
                               }
                               )
    except ssl.SSLError:
        translation = ['']
        print("Error at translate_sys. Read operation timed out")
        return translation
    try:
        translation = response.body['outputs'][0]['output']
        translation_conf = response.body['outputs'][0]['detectedLanguageConfidence']
    except KeyError:
        print("Error at translate_sys. Unknown output: %s" % response.body)
        print("Input url:" + url)
        translation = ['']
    return translation


# Return meaning of Japanese word in English, with same bounding box
def get_translation_pair(allergy_word_jp, allergy_list_jp_en):
    # Get translation pair
    allergy_word_eng_word = list()
    allergy_word_eng_bb = list()
    for i in range(len(allergy_word_jp['word'])):
        eng_word = allergy_list_jp_en[allergy_word_jp['word'][i]]
        eng_word_bb = allergy_word_jp['bb'][i]
        allergy_word_eng_word.append(eng_word)
        allergy_word_eng_bb.append(eng_word_bb)
    return {'word': allergy_word_eng_word, 'bb': allergy_word_eng_bb}


# Given list of string and a string, return list of index where "word" exist
def get_index(list_of_word, word):
    index = list()
    for i, j in enumerate(list_of_word):
        if j == word:
            index.append(i)
    return index


# Given a list of string, return only elements which exist in text
def check_exist(word_list, text):
    exist_word = list()
    for word in word_list:
        if word in text:
            exist_word.append(word)
    return exist_word


# Get values (english word) from allergy_pair
def get_english_allergy_list(allergy_pair):
    english_allergy_list = list()
    for value in allergy_pair.values():
        for w in value:
            english_allergy_list.append(w)
    english_allergy_list = list(set(english_allergy_list))
    return english_allergy_list


# Convert list of japanese characters into full string, can have delimiter between elements
def word_list_to_str(word_list, delimiter=''):
    word = ''
    for count, letter in enumerate(word_list):
        if count != len(word_list) - 1:
            word = word + letter + delimiter
        else:
            word = word + letter
    return word


# Check all elements in all_word, return all element which exist in allergy list
def check_allergy(all_word, aller_list):
    allergy_word = list()
    allergy_word_bb = list()
    for allergy in aller_list:  # allergy = '海老'
        matched_word_index = get_index(all_word['word'], allergy[0])  # position of word of 海 e.g. [5, 11]
        if len(matched_word_index) > 0:  # Check if there's word exist
            for checked_position in matched_word_index:  # checked_position = 5
                combined_word = ''
                combined_word_bb = list()
                for cnt in range(checked_position, checked_position + len(allergy)):  # cnt = 5,6
                    if cnt >= len(all_word['word']):  # stop if it's over the length of the word
                        break
                    combined_word = combined_word + all_word['word'][cnt]  # Combine words from the interested point
                    combined_word_bb.append(all_word['bb'][cnt])
                if combined_word == allergy:  # Compare combined word with the allergy, include if equal
                    allergy_word.append(combined_word)
                    allergy_word_bb.append(combined_word_bb)
    return {'word': allergy_word, 'bb': allergy_word_bb}


# Check elements that co-exist between two lists
def cross_check(ocr_list, trans_list_one, trans_list_two):
    # Flatten ocr_list and Remove duplicates
    ocr_list_temp = [item for sublist in ocr_list for item in sublist]
    ocr_list = list(set(ocr_list_temp))
    word_list_one = list(set(trans_list_one))
    word_list_two = list(set(trans_list_two))

    result = {'exist_3': list(), 'exist_2': list(), 'exist_1': list()}

    for word in ocr_list:
        count = 1
        if word in word_list_one:
            count = count + 1
            word_list_one.remove(word)
        if word in word_list_two:
            count = count + 1
            word_list_two.remove(word)
        name = 'exist_' + str(count)
        result[name].append(word)
    for word in word_list_one:
        count = 1
        if word in word_list_two:
            count = count + 1
            word_list_two.remove(word)
        name = 'exist_' + str(count)
        result[name].append(word)
    for word in word_list_two:
        count = 1
        name = 'exist_' + str(count)
        result[name].append(word)
    return {'result': result}


# Given two dictionaries with same keys, combined together
def merge_result(result_main, result):
    result_new_temp = {'exist_3': result_main['exist_3'] + list(set(result['exist_3']) - set(result_main['exist_3'])),
                       'exist_2': result_main['exist_2'] + list(set(result['exist_2']) - set(result_main['exist_2'])),
                       'exist_1': result_main['exist_1'] + list(set(result['exist_1']) - set(result_main['exist_1']))}

    result_new = {'exist_3': result_new_temp['exist_3'],
                  'exist_2': list(set(result_new_temp['exist_2']) - set(result_new_temp['exist_3'])),
                  'exist_1': list(set(result_new_temp['exist_1']) - set(result_new_temp['exist_2']) - set(
                      result_new_temp['exist_3']))}
    return result_new


# Main Function for us
def translate_jp_region(ocr_word, allergies):
    ingredient_char = [u'原', u'材', u'料', u'名']
    # List of allergies with their meaning
    standard_allergy_pair = {u'海老': ['shrimp', 'prawn'],
                             u'エビ': ['shrimp', 'prawn'],
                             u'えび': ['shrimp', 'prawn'],
                             u'かに': ['crab'],
                             u'小麦': ['wheat', 'flour'],
                             u'そば': ['buckwheat', 'soba'],
                             u'卵': ['egg'],
                             u'たまご': ['egg'],
                             u'乳': ['milk'],
                             u'落花生': ['peanut'],
                             u'あわび': ['abalone'],
                             u'いか': ['squid'],
                             u'いくら': ['salmon roe'],
                             u'オレンジ': ['orange'],
                             u'カシューナッツ': ['cashew nut'],
                             u'キウイフルーツ': ['kiwifruit'],
                             u'牛肉': ['beef'],
                             u'くるみ': ['walnuts'],
                             u'ごま': ['sesame'],
                             u'鮭': ['salmon'],
                             u'さけ': ['salmon'],
                             u'さば': ['mackerel'],
                             u'大豆': ['soybeans'],
                             u'鶏肉': ['chicken'],
                             u'バナナ': ['banana'],
                             u'豚肉': ['pork'],
                             u'まつたけ': ['matsutake'],
                             u'もも': ['peaches'],
                             u'やまいも': ['yams'],
                             u'りんご': ['apple'],
                             u'ゼラチン': ['gelatin']}

    # Get only interested allergy words (from user)
    if allergies is None:
        allergy_pair_jp_en = standard_allergy_pair
    elif len(allergies) == 0:
        allergy_pair_jp_en = standard_allergy_pair
    else:
        allergy_pair_jp_en = filter_values(standard_allergy_pair, allergies)
    allergy_list_eng = get_english_allergy_list(allergy_pair_jp_en)

    # Check if there is word "ingredients inside", return boolean (Should be True)
    keyword_exist = check_keyword(ingredient_char, ocr_word)
    if not keyword_exist:
        result = {"error": "Ingredients not found"}
    else:
        # Compare ocr result with allergy list, output is dictionary
        ocr_allergy_jp = check_allergy(ocr_word, allergy_pair_jp_en.keys())
        # Get translation of allergies in English, output is dictionary
        ocr_allergy_en = get_translation_pair(ocr_allergy_jp, allergy_pair_jp_en)
        # Translate detected word into English
        translation_micr = translate_microsoft(word_list_to_str(ocr_word['word']))  # Takes 1.6 sec
        translation_syst = translate_sys(word_list_to_str(ocr_word['word']))  # Takes 1.85 sec
        # Check if allergy word exist in the translation or not
        translate_allergy_micr = check_exist(allergy_list_eng, translation_micr)
        translate_allergy_syst = check_exist(allergy_list_eng, translation_syst)
        # Check between three methods, give confidence level
        result = cross_check(ocr_allergy_en['word'], translate_allergy_micr, translate_allergy_syst)
        # Print allergies word
        # print("OCR Allergies word(JP) result: " + word_list_to_str(ocr_allergy_jp['word'], ','))
        # print("OCR Allergies word(EN) result: " + str(ocr_allergy_en['word']))
        # print("Translated allergies word(Microsoft) result: " + str(translate_allergy_micr))
        # print("Translated allergies word(Systran) result: " + str(translate_allergy_syst))
    return result


def translate_en_region(ocr_word):  # Not using right now
    allergy_list_eng = ['shrimp', 'crab', 'wheat', 'soba', 'egg', 'milk', 'peanut']  # Temp
    ocr_allergy = check_exist(ocr_word['word'], allergy_list_eng)  # Note that we lose bounding box info here
    result = {"result": ocr_allergy}
    return result


# For other language, we use APIs to translate english word to another language and cross-check with OCR
def translate_other_region(ocr_word, allergy_list_en, language):
    # keyword = "name of ingredient"
    # Get list of allergies in desired language
    if allergy_list_en is None:
        allergy_list_en = ['shrimp', 'crab', 'wheat', 'soba', 'egg', 'milk', 'peanut']
    elif len(allergy_list_en) == 0:
        allergy_list_en = ['shrimp', 'crab', 'wheat', 'soba', 'egg', 'milk', 'peanut']
    allergy_string_en = word_list_to_str(allergy_list_en, delimiter='_')
    allergy_string_other = translate_sys(allergy_string_en, language)
    allergy_list_other = allergy_string_other.split('_')
    # print("Detect other language: %s" % language)
    if len(allergy_list_other) != len(allergy_list_en):
        raise ValueError("Translation conflited. Input as language: %s, Message: %s" % (language, ocr_word))
    # Create allergy pair as same as translate_jp
    allergy_pair = {}
    for i, value in enumerate(allergy_list_en):
        allergy_pair[allergy_list_other[i]] = value

    # Compare ocr result with allergy list, output is dictionary
    ocr_allergy_other = check_allergy(ocr_word, allergy_list_other)
    # Get translation of allergies in English, output is dictionary
    ocr_allergy_en = get_translation_pair(ocr_allergy_other, allergy_pair)
    # Translate detected word into English
    translation_micr = translate_microsoft(word_list_to_str(ocr_word['word']))  # Takes 1.6 sec
    translation_syst = translate_sys(word_list_to_str(ocr_word['word']))  # Takes 1.85 sec
    # Check if allergy word exist in the translation or not
    translate_allergy_micr = check_exist(allergy_list_en, translation_micr)
    translate_allergy_syst = check_exist(allergy_list_en, translation_syst)
    result = cross_check(ocr_allergy_en['word'], translate_allergy_micr, translate_allergy_syst)
    # Print allergies word
    # print("OCR Allergies word(%s) result: " % language) result: " + word_list_to_str(ocr_allergy_other['word'], ','))
    # print(("OCR Allergies word(EN) + str(ocr_allergy_en['word']))
    # print("Translated allergies word(Microsoft) result: " + str(translate_allergy_micr))
    # print("Translated allergies word(Systran) result: " + str(translate_allergy_syst))
    return result


# Based on ocr, we split set of text into regions, we translate one region and a time
def translate_jp(ocr_words, allergies):
    total_result = {'exist_3': [], 'exist_2': [], 'exist_1': []}
    count = 0
    for i in range(len(ocr_words)):
        region_result = translate_jp_region(ocr_words[i], allergies)
        if 'error' in region_result:  # If not found keyword, skip doing the rest
            count = count + 1
            break
        # Combined result from the current one with the previous one
        total_result = merge_result(total_result, region_result['result'])
    if (count == len(ocr_words)) and (count != 0):
        total_result = {"error": "Ingredients not found"}
    return {'result': total_result}


def translate_en(ocr_words):  # Unused Function
    result = list()
    for i in range(len(ocr_words)):
        region_result = translate_en_region(ocr_words[i])
        result = result + list(set(region_result) - set(result))
    return {'result': result}


def translate_other(ocr_words, allergies, language):
    total_result = {'exist_3': [], 'exist_2': [], 'exist_1': []}
    count = 0
    for i in range(len(ocr_words)):
        region_result = translate_other_region(ocr_words[i], allergies, language)
        if 'error' in region_result:  # If not found keyword, skip doing the rest
            count = count + 1
            break
        # Combined result from the current one with the previous one
        total_result = merge_result(total_result, region_result['result'])
    if (count == len(ocr_words)) and (len(ocr_words) != 0):
        total_result = {"error": "Cannot translate allergies name. This language is not supported (%s)" % language}
    return {'result': total_result}


# Determine function based on language detected
def get_allergies(url_link, allergies=None):
    ocr_word, language = ocr(url_link)  # Take 2.67 secx
    if language == 'unk':
        result = {'error': "No text detected"}
    elif language == 'ja':  # For default
        result = translate_jp(ocr_word, allergies)
    elif language == 'en':  # Not supported yet
        result = {'error': "No japanese detected"}
    else:  # For other language
        result = translate_other(ocr_word, allergies, language)
    return result


if __name__ == '__main__':
    # url_link = "https://res.cloudinary.com/pasink/image/upload/v1550237262/test_hd.jpg"  # First Sample
    # url_link = "https://res.cloudinary.com/pasink/image/upload/v1550300203/test2.jpg"  # Second Sample, MS error
    # url_link = "https://res.cloudinary.com/pasink/image/upload/v1550289399/vertical1.jpg" # Not found Sample
    # url_link = "https://res.cloudinary.com/pasink/image/upload/v1550278845/korean.jpg"  # Korean file
    url_link = "https://allergynode.herokuapp.com/photos/test-photo.jpg"

    final_result = get_allergies(url_link=url_link, allergies=None)
    print(final_result)
