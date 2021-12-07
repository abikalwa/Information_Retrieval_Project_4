from itertools import count
from flask import Flask, render_template, request, url_for, redirect
import json
import re
import urllib.request
from urllib.parse import quote
from googletrans import Translator
translator = Translator()
# from langdetect import detect

app = Flask(__name__)

@app.route("/", methods=["POST","GET"])
def main():
    if request.method=="POST":
        query=request.form['search']
        language=request.form['language']
        country=request.form['country']
        poi=request.form['poi']
        print(query)
        hashtags = re.findall(r"#(\w+)", query)
        hashtags = str(hashtags)
        hashtags = hashtags.replace('[','')
        hashtags = hashtags.replace(']','')
        hashtags = quote(hashtags)
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
        
        solr_ip_address = 'http://54.172.188.129:8983/solr/'
        CORE_NAME = "IRF21P4"
        # change the url according to your own corename and query
        inurl = solr_ip_address + CORE_NAME + '/select?q='+'text_en'+'%3A'+query+'%0A'+'text_es'+'%3A'+query+'%0A'+'text_hi'+'%3A'+query+'&rows=1000000&wt=json'
        print(inurl)
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


        if poi_filtered_tweet=="":
            poi_filtered_tweet.append("No tweets to show!!")
        else:
            final_filtered_tweets=[]
            for i in poi_filtered_tweet:
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
                final_filtered_tweets.append(indv_tweets)

        return render_template('home.html',tweetlist=final_filtered_tweets)
    else:
        return render_template("home.html"); 
    

if __name__=="__main__":
    app.debug=True
    app.run(debug=True, host='0.0.0.0')