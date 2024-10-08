from flask import Flask, render_template, request, redirect, url_for, flash
import requests
from bs4 import BeautifulSoup
import re
import json
from db_config import get_db_connection
import random
import math

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

# Function to fetch all projects
def fetch_projects():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT id, projectName FROM Project"
    cursor.execute(query)
    projects = cursor.fetchall()
    cursor.close()
    connection.close()
    return projects

# Function to fetch properties under multiple projects
def fetch_properties_by_projects(project_ids):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT id, propertyType AS type, state, address, price, numberOfBedrooms AS bedrooms FROM Property WHERE ProjectId IN (%s)" % ','.join(['%s'] * len(project_ids))
    cursor.execute(query, project_ids)
    properties = cursor.fetchall()
    cursor.close()
    connection.close()
    print(f"Fetched properties: {properties}")  # Debugging line
    return properties


# Function to load templates
def load_templates(filepath='templates.json'):
    with open(filepath, 'r') as file:
        templates = json.load(file)
    return templates

# Function to generate descriptions for properties
def generate_description(property, templates):
    property_type = property['type']
    if property_type not in templates:
        return None  
    
    # Select a random template
    description_template = random.choice(templates[property_type])
    description_template = description_template.replace('[bedrooms]', '{bedrooms}').replace('[location]', '{location}')
    description = description_template.format(
        bedrooms=property['bedrooms'],
        location=property['address'] + ',' + property['state'],
    )
    return description

# Function to fetch the current average price using web scraping
def fetch_average_price(property):
    url = f"https://nigeriapropertycentre.com/for-sale/{property['type']}/{property['state']}/showtype?bedrooms={property['bedrooms']}"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'lxml')
        price_tags = soup.find_all('span', class_='price')
        prices = []
    
        for tag in price_tags:
            content = tag.get('content')
            if content and re.search(r'\d', content):  
                price = int(re.sub(r'[^\d]', '', content))
                prices.append(price)

        if prices:
            # Calculate the average price
            average_price = sum(prices) / len(prices)
            # Round up to the nearest million
            average_price_rounded = math.ceil(average_price / 1_000_000) * 1_000_000
            return average_price_rounded
          
        else:
            return None
    else:
        return None

# Function to update property description and price in the database
def update_property(property_id, description ):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "UPDATE Property SET description = %s WHERE id = %s"
    cursor.execute(query, (description, property_id))
    connection.commit()
    cursor.close()
    connection.close()

@app.route('/')
def index():
    projects = fetch_projects()  # Fetch all projects
    return render_template('index.html', projects=projects)

# Route to handle the update process after selecting multiple projects
@app.route('/update-properties', methods=['POST'])
def update_properties():
    selected_projects = request.form.getlist('projects')  # Get selected project IDs
    properties = fetch_properties_by_projects(selected_projects)  # Fetch properties for the selected projects
    templates = load_templates()  # Load the templates
    
    updated_properties = []  # To store updated properties
    
    for property in properties:
        description = generate_description(property, templates)
        # price = fetch_average_price(property)  # Fetch average price using web scraping
        
        if description:  # Make sure both description and price are available
            update_property(property['id'], description)  # Update each property in the database
            
            # Add description and price to the property object before rendering
            property['description'] = description
            
            updated_properties.append(property)  # Track updated properties
    
    # Flash success message
    flash('Properties have been successfully updated!', 'success')
    
    # Pass updated properties (with descriptions and prices) to the template
    return render_template('updated_properties.html', properties=updated_properties)


# Result page for displaying updated properties
@app.route('/updated-properties')
def updated_properties():
    return render_template('updated_properties.html')

if __name__ == '__main__':
    port = 5000 
    app.run(host='0.0.0.0', port=port)
