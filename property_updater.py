import requests
from bs4 import BeautifulSoup
import re
import json
from db_config import get_db_connection
import random

def load_templates(filepath='templates.json'):
    with open(filepath, 'r') as file:
        templates = json.load(file)
    return templates

def fetch_properties(id_min, id_max):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT id, propertyType AS type, state, address, numberOfBedrooms AS bedrooms FROM Property WHERE id BETWEEN %s AND %s"
    cursor.execute(query, (id_min, id_max))
    properties = cursor.fetchall()
    cursor.close()
    connection.close()
    return properties

# Function to customize the template
def generate_description(property, templates):
    property_type = property['type']
    if property_type not in templates:
        return None  
    
    # Select a random template
    description_template = random.choice(templates[property_type])
    description_template = description_template.replace('[bedrooms]', '{bedrooms}').replace('[location]', '{location}')
    description = description_template.format(
        bedrooms=property['bedrooms'],
        location= property['state'],
    )
    return description

# Function to fetch the current average price using web scraping
def fetch_average_price(property):
    # url = f"https://nigeriapropertycentre.com/for-sale/houses/{property['state']}/{property['address']}/showtype?bedrooms={property['bedrooms']}"
    url = f"https://nigeriapropertycentre.com/for-sale/houses/abuja/galadimawa/showtype?bedrooms=4"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'lxml')
        price_tags = soup.find_all('span', class_='price')
        print(price_tags)
        prices = []
    
        for tag in price_tags:
            content = tag.get('content')
            if content and re.search(r'\d', content):  
                price = int(re.sub(r'[^\d]', '', content))
                price = round(float(price))
                prices.append(price)
        print(prices)
        print(sum(prices) / len(prices))
        return sum(prices) / len(prices) if prices else None
    else:
        return None


# Function to update property description and price in the database
def update_property(property_id, description):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "UPDATE Property SET description = %s WHERE id = %s"
    cursor.execute(query, (description, property_id))
    connection.commit()
    cursor.close()
    connection.close()

# Main function
def update_properties(id_min, id_max):
    properties = fetch_properties(id_min, id_max)
    templates = load_templates()
    
    for property in properties:
        description = generate_description(property, templates)
        print(description)
        if not description:
            print(f"No template found for property type {property['type']}")
            continue
    
        # average_price = fetch_average_price(property)
        # if not average_price:
        #     print(f"Could not fetch price for property in {property['state']}")
        #     continue
        print(property['id'], description)
        # Update the property in the database
        update_property(property['id'], description)
        print(f"Updated property {property['id']} with new description and price.")

# Example usage: User specifies ID range
id_min = int(input("Enter the minimum ID: "))
id_max = int(input("Enter the maximum ID: "))

# Run the automation process with the dynamic ID range
update_properties(id_min, id_max)

