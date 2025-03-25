import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import math
import faiss
import numpy as np
import pandas as pd
from common_helper import create_embedding

class Indexer:
    MODEL_CHUNK_SIZE = 8192

    def __init__(self, index_file, metadata_file, embedding_dim):
        self.index_file = index_file
        self.metadata_file = metadata_file
        self.embedding_dim = embedding_dim  # Adjust based on your embedding model
        
        # Try loading Faiss index, else create a new one
        try:
            self.index = faiss.read_index(self.index_file)
            self.metadata_df = pd.read_csv(self.metadata_file)
            print("✅ Faiss index & metadata loaded successfully!")
        except:
            self.index = faiss.IndexFlatIP(self.embedding_dim)  # IP Distance for similarity
            self.metadata_df = pd.DataFrame(columns=["text", "path"])
            print("⚠️ No existing index found. Creating a new one.")

    def get_html_sitemap(self, url):
        print(f"---run---{url}")
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "xml")

        links = [loc.get_text() for loc in soup.find_all("loc")]
        for url in links:
            print(f"🔗 Found URL: {url}")

        return links

    def get_html_body_content(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        return soup.body.get_text()

    def index_website(self, website_url):
        print(f"🔍 Indexing website: {website_url}")
        shop_links = ["https://shop.cryptnox.com/",
                "https://shop.cryptnox.com/products/walletconnect-hardware-wallet-card-dual",
                "https://shop.cryptnox.com/products/cryptnox-fido-2-card",
                "https://shop.cryptnox.com/products/cryptnox-rfid-nfc-contactless-blocking-card",
                "https://shop.cryptnox.com/products/contactless-smart-card-reader-iso-14443-mifare%C2%AE-compliant-usb-type-c-and-type-a-connectivity-secure-authentication-for-e-payments-e-commerce-access-control-more",
                "https://shop.cryptnox.com/products/cryptnox%C2%AE-usb-smart-card-cac-reader-for-computer-compatible-with-windows-10-and-linux-common-access-card-reader-usb-2-0-full-speed-pc-sc-2-0-standard",
                ]
        # main_links = self.get_html_sitemap(website_url)
        with open("links.txt", "r") as file:
            main_links = file.readlines()
        print(main_links)
        links = shop_links + main_links
        print(f"🔗 Total URLs to process: {len(links)}")
        for link in links:  # Limit to 10 for demonstration
            print(f"🔗 Processing {link}")
            try:
                content = self.get_html_body_content(link)
                self.add_html_to_vectordb(content, link)
            except Exception as e:
                print(f"❌ Unable to process {link}: {e}")

    def add_html_to_vectordb(self, content, path):
        content = content.replace("\n\n", " ")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.MODEL_CHUNK_SIZE,
            chunk_overlap=math.floor(self.MODEL_CHUNK_SIZE / 10)
        )

        docs = text_splitter.create_documents([content])
        for doc in docs:
            embedding = create_embedding(doc.page_content)
            self.insert_embedding(embedding, doc.page_content, path)

    def insert_embedding(self, embedding, text, path):
        # Convert embedding to NumPy float32 format
        vector = np.array(embedding, dtype=np.float32).reshape(1, -1)
        # Add to Faiss index
        self.index.add(vector)
        # Store metadata
        new_data = pd.DataFrame([{"text": text, "path": path}])
        self.metadata_df = pd.concat([self.metadata_df, new_data], ignore_index=True)
        # Save index & metadata
        faiss.write_index(self.index, self.index_file)
        self.metadata_df.to_csv(self.metadata_file, index=False)

        print(f"✅ Inserted: {text[:50]}... ({path})")
