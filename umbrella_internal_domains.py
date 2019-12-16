#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script is used to synchronize domains listed in a CSV file to Umbrella Internal Domains.

This will cause Umbrella Virtual Appliances and Roaming Clients to pass-through DNS lookups for
those domains, resulting in the local DNS resolution.
"""

import argparse
import csv
import json
import os
import time

import requests

from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

csv_domains = []


def load_csv():
    """
    This function loads domains from the specified CSV file.
    """

    print("Importing CSV File...")

    try:
        # Get the desired file name
        file_name = os.getenv("CSV_FILENAME")

        # Try to read the specified CSV file
        with open(file_name) as csv_file:
            csv_reader = csv.reader(csv_file)

            # Add each domain to a list
            for domain in csv_reader:
                csv_domains.append(domain[0])

    except:
        print(f"There was an issue reading the specified filename '{file_name}'.")
        print("Please check the CSV_FILENAME configuration in the '.env' file, and verify the file format.")
        exit(1)

    print(f"CSV file successfully imported.")


def get_umbrella_internal_domains():
    """
    Get the Internal Domains from Umbrella
    """

    print("Getting all Internal Domains from Umbrella.")

    # Build the API URL
    api_url = f"https://management.api.umbrella.com/v1/organizations/{os.getenv('UMBRELLA_API_ORG_ID')}/internaldomains"

    try:
        # Get the Umbrella Internal Domains
        request = requests.get(api_url, auth=HTTPBasicAuth(os.getenv("UMBRELLA_API_MANAGEMENT_KEY"), os.getenv("UMBRELLA_API_MANAGEMENT_SECRET")))

        # Check to make sure the GET was successful
        if request.status_code == 200:
            print("Internal Domains successfully retrieved.")
            return request.json()
        else:
            print(f"Umbrella Connection Failure - HTTP Return Code: {request.status_code}\nResponse: {request.text}")
            exit(1)
    except Exception as exception:
        print(exception)
        exit(1)


def post_umbrella_internal_domain(domain):
    """
    Post a new Internal Domain to Umbrella
    """

    print(f"Adding Internal Domain '{domain}' to Umbrella.")

    # Build the API URL
    api_url = f"https://management.api.umbrella.com/v1/organizations/{os.getenv('UMBRELLA_API_ORG_ID')}/internaldomains"

    # Build the POST data
    data = {
        "domain": domain
    }

    try:
        # Post the Umbrella Internal Domains
        request = requests.post(api_url,
                                auth=HTTPBasicAuth(os.getenv("UMBRELLA_API_MANAGEMENT_KEY"), os.getenv("UMBRELLA_API_MANAGEMENT_SECRET")),
                                data=json.dumps(data))

        # Check to make sure the POST was successful
        if request.status_code == 200:
            print("Successfully added Internal Domain to Umbrella.")
            return request.json()
        else:
            print(f"Umbrella Connection Failure - HTTP Return Code: {request.status_code}\nResponse: {request.text}")
            exit(1)
    except Exception as exception:
        print(exception)
        exit(1)


def main():
    """
    This is the main function to run the logic of the Internal Domain importer.
    """

    # Load the CSV file
    load_csv()

    # Get the current Umbrella Internal Domains
    umbrella_domains = get_umbrella_internal_domains()

    temp_list = []

    # Format the Umbrella Internal Domains
    for internal_domain in umbrella_domains:
        temp_list.append(internal_domain['domain'])

    umbrella_domains = temp_list

    # Get a list of domains that are in our CSV that don't exist in Umbrella
    pending_domains = list(set(csv_domains) - set(umbrella_domains))

    # Add each pending domain to Umbrella Internal Domains
    for new_domain in pending_domains:
        post_umbrella_internal_domain(new_domain)

if __name__ == "__main__":

    # Set up an argument parser
    parser = argparse.ArgumentParser(description="A script to import a list of domains into Umbrella as Internal Domains")
    parser.add_argument("-d", "--daemon", help="Run the script as a daemon", action="store_true")
    args = parser.parse_args()

    if args.daemon:

        # Refresh Interval
        interval = int(os.getenv("INTERVAL"))

        while True:
            main()
            print(f"Waiting {interval} seconds...")
            time.sleep(interval)
    else:
        main()
