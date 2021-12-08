from itertools import count
from flask import Flask, render_template, request, url_for, redirect
import json
import re
import urllib.request
from urllib.parse import quote
from translate import Translator
from textblob import TextBlob
# from langdetect import detect

app = Flask(__name__)

def clean_tweet(tweet):
        '''
        Utility function to clean tweet text by removing links, special characters
        using simple regex statements.
        '''
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

@app.route("/", methods=["POST","GET"])
def main():
    if request.method=="POST":
        query=request.form['search']
        language=request.form['language']
        country=request.form['country']
        poi=request.form['poi']
        # print(query)
        for letter in query:
            if letter in {'~', ':', "'", '-', ',', '&', '.',  ';', '?',"'",}:
                query = query.replace(letter," ")   
        # hashtags = hashtags.replace(" ",'')
        # hashtags = hashtags.replace('/"','')
        
        # print(hashtags)
        
        query = query.replace(':','')
        query = quote(query)
        # print(query)

        if language=='hindi':
            lang='text_hi'
        if language=='english':
            lang='text_en'
        if language=='spanish':
            lang='text_es'
        
        if country=='india':
            country='India'
        if country=='mexico':
            country='Mexico'
        if country=='usa':
            country='USA'
        
        solr_ip_address = 'http://54.163.180.165:8983/solr/'
        
        # check_for_replies = 'http://52.90.220.99:8983/solr/IRF21P4/select?q=*%3A*&wt=json'
        # connect_for_replies = urllib.request.urlopen(check_for_replies)
        # total_data = json.load(connect_for_replies)['response']['docs']
        poi_reply=[]
        for pr in range(1,12):
            with open('C:/Users/mohitsee/Documents/Information_Retrieval/Project_4/project_folder/static/reply_keyword_'+str(pr)+'.json') as json_file:
                poi_reply+=json.load(json_file)
        keyword_reply=[]
        for kr in range(1,16):
            with open('C:/Users/mohitsee/Documents/Information_Retrieval/Project_4/project_folder/static/reply_'+str(kr)+'.json') as json_file:
                keyword_reply+=json.load(json_file)
        total_data=poi_reply+keyword_reply
        # print(len(total_data))

        # for k in total_data:
        #     if k['replied_to_tweet_id']==1440293420212260877:
        #         print("success")

        CORE_NAME = "IRF21P4"
        # change the url according to your own corename and query
        inurl = solr_ip_address + CORE_NAME + '/select?q='+'text_en'+'%3A'+query+'%0A'+'text_es'+'%3A'+query+'%0A'+'text_hi'+'%3A'+query+'&rows=1000000&wt=json'
        # print(inurl)
        data = urllib.request.urlopen(inurl)
        # print(json.load(data))
        docs = json.load(data)['response']['docs']
        poi_tweet_list=[]
        nonpoi_tweet_list=[]
        for i in docs:
            if 'poi_name' in list(i.keys()):
                poi_tweet_list.append(i)
            else:
                nonpoi_tweet_list.append(i)
        final_tweet_list=poi_tweet_list+nonpoi_tweet_list


        ReTweet_filtered_tweet=[]
        for i in final_tweet_list:
            for j in list(i.keys()):
                if 'text_' in j:
                    cleaned_tweet_text=j
                    break
            if i[cleaned_tweet_text]!="" and i[cleaned_tweet_text][:2]!='RT':
                ReTweet_filtered_tweet.append(i)     

        lang_filtered_tweet=[]
        if language!="null":
            for i in ReTweet_filtered_tweet:
                if 'text_'+i['tweet_lang']==lang:  
                    lang_filtered_tweet.append(i) 
        else:
            lang_filtered_tweet=ReTweet_filtered_tweet

        country_filtered_tweet=[]
        if country!="null":
            for i in lang_filtered_tweet:
                if i['country']==country:  
                    country_filtered_tweet.append(i)
        else:
            country_filtered_tweet=lang_filtered_tweet        

        poi_filtered_tweet=[]
        if poi!="null":
            for i in country_filtered_tweet:
                if 'poi_name' in list(i.keys()) and i['poi_name']==poi:
                    poi_filtered_tweet.append(i)
        else:
            poi_filtered_tweet=country_filtered_tweet    
        
        # print(len(poi_filtered_tweet))

        final_filtered_tweets=[]
        if poi_filtered_tweet!=[]:
            for i in poi_filtered_tweet:
                # print(i['id'])
                indv_tweets={}
                for j in list(i.keys()):
                    if 'text_' in j:
                        cleaned_tweet_text=j
                        break
                if 'poi_name' in list(i.keys()):
                    indv_tweets['poi_name']='@'+i['poi_name']
                else:
                    indv_tweets['poi_name']=''
                topic_highlights=[]
                if 'hashtags' in list(i.keys()):
                    topic_highlights+=i['hashtags']
                if 'mentions' in list(i.keys()):
                    topic_highlights+=i['mentions']
                if topic_highlights!=[]:
                    indv_tweets['topics']=topic_highlights
                else:
                    indv_tweets['topics']=[]
                
                indv_tweets['tweet_text']=i[cleaned_tweet_text]
                if i['tweet_lang']=='es':
                    translator=Translator(from_lang='spanish', to_lang='english')
                    translated_tweet = translator.translate(i['tweet_text'])
                elif i['tweet_lang']=='hi':
                    translator=Translator(from_lang='hindi', to_lang='english')
                    translated_tweet = translator.translate(i['tweet_text'])
                elif i['tweet_lang']=='en':
                    translated_tweet = i['tweet_text']
                else:
                    translator=Translator(to_lang='english')
                    translated_tweet = translator.translate(i['tweet_text'])

                # print(translated_tweet," Translated")
                analysis = TextBlob(clean_tweet(translated_tweet))
                # set sentiment
                if analysis.sentiment.polarity > 0:
                    indv_tweets['sentiment']='positive'
                elif analysis.sentiment.polarity == 0:
                    indv_tweets['sentiment']='neutral'
                else:
                    indv_tweets['sentiment']='negative'
                indv_tweets['sentiment_score']=analysis.sentiment.polarity

                list_of_replies=[]
                for k in total_data:
                    # print(k['replied_to_tweet_id'],i['id'])
                    # print(type(k['replied_to_tweet_id']))
                    if k['replied_to_tweet_id']==int(i['id']):
                        list_of_replies.append(k)
                top_pstve_replies=[]
                top_ngtve_replies=[]
                max=-1 
                min=1
                cleaned_replies=[]
                templist_for_replies=[]
                for k in list_of_replies:
                    if k['tweet_lang']=='es':
                        translator=Translator(from_lang='spanish', to_lang='english')
                        translated_tweet = translator.translate(k['tweet_text'])
                    elif k['tweet_lang']=='hi':
                        translator=Translator(from_lang='hindi', to_lang='english')
                        translated_tweet = translator.translate(k['tweet_text'])
                    elif k['tweet_lang']=='en':
                        translated_tweet = k['tweet_text']
                    else:
                        translator=Translator(to_lang='english')
                        translated_tweet = translator.translate(k['tweet_text'])
                    sent_analysis = TextBlob(clean_tweet(translated_tweet))
                    cleaned_replies.append(sent_analysis)
                    templist_for_replies.append(k['tweet_text'])
                    if sent_analysis.sentiment.polarity>max:
                        max=sent_analysis.sentiment.polarity
                    if sent_analysis.sentiment.polarity<min:
                        top_ngtve_replies.append(k['tweet_text'])
                        min=sent_analysis.sentiment.polarity
                for sent_reply,reply in zip(cleaned_replies,templist_for_replies):
                    if sent_reply.sentiment.polarity==max and sent_reply.sentiment.polarity>0 and reply not in top_pstve_replies:
                        top_pstve_replies.append(reply)
                    elif sent_reply.sentiment.polarity==min and sent_reply.sentiment.polarity<0 and reply not in top_ngtve_replies:
                        top_ngtve_replies.append(reply)
                indv_tweets['Top Positive Replies']=top_pstve_replies
                indv_tweets['Top Negative Replies']=top_ngtve_replies
                tweet_url='https://twitter.com/twitter/statuses/'+i['id']
                indv_tweets['tweet_url']=tweet_url
                indv_tweets['country']=i['country']
                indv_tweets['language']=i['tweet_lang']
                indv_tweets['verified']=i['verified']
                final_filtered_tweets.append(indv_tweets)
        else:
            final_filtered_tweets.append("No tweets to show!!")

        return render_template('home.html',tweetlist=final_filtered_tweets)
    else:
        return render_template("home.html"); 
    

if __name__=="__main__":
    app.debug=True
    app.run(debug=True, host='0.0.0.0')