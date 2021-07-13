import requests
import json
import datetime as dt
from requests.auth import HTTPBasicAuth


def write_json_file(file_path, config):
    with open(file_path, 'w') as f:
        json.dump(config, f, indent=4)


def read_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


def login():
    file = open('config.json')
    config = json.load(file)
    auth_url = 'https://www.apimall.acra.gov.sg/authorizeServer/oauth/token?grant_type=client_credentials'
    response = requests.post(auth_url,
                             auth=HTTPBasicAuth(config['username'], config['password']))

    config['accessToken'] = response.json()['access_token']
    write_json_file('config.json', config)
    print('Successful log in and access token received')
    # print(config['accessToken'])


def reformat_date_to_mm_dd_yy(date):
    # Good: 06/30/2019
    example_date = date
    new_date = example_date.replace('-', '')
    temp = dt.datetime.strptime(new_date, '%Y%m%d')
    final_date = temp.strftime('%m/%d/%Y')
    # print(final_date)

    return final_date


def reformat_date_to_yyyy_mm_dd(date):
    # Good: '2019-12-31'
    # From: 06/30/19

    # Prep the date
    if date[1] == '/':
        date = '0' + date
    if date[4] == '/':
        date = date[:3] + '0' + date[3:]

    new_date = date.replace('/', '')
    temp = dt.datetime.strptime(new_date, '%m%d%y')
    final_date = temp.strftime('%Y-%m-%d')

    return final_date


def add_to_csv(res1, res2):
    print(res1)
    print(res2)

    r1 = res1['entities'][0]
    r2 = res2['entities'][0]

    date = reformat_date_to_mm_dd_yy(r1['fyeDate'])

    # Create a new line with all the details from both API calls.

    # LINES INCOMPLETE. GROUP VS COMPANY

    # GROUP TYPE RESPONSE
    line = []
    modified_uen = r1['uen'] + ' (' + r1['name'] + ') ' + date
    if r1['accType'] == 'GROUP':
        line = [modified_uen, r1['name'], date, r1['groupTotalAssets'], r2['groupTotalCurrentAssets'],
                r1['groupTotalLiabilities'], r2['groupTotalCurrentLiabilities'],
                r1['groupTotalEquities'], r1['revenue'],
                r2['groupRetainedEarningsAccumulatedLoss'], r2['ebit'],
                r1['profitLossBeforeTaxFromContinuingOperations'], r1['profitLossAfterTaxFromContinuingOperations']]
    elif r1['accType'] == 'COMPANY':
        # ////NOTE///// Spelling error with liabilities, error on part of ACRA
        line = [modified_uen, r1['name'], date, r1['companyTotalAssets'], r2['companyTotalCurrentAssets'],
                r1['companyTotalLiabilities'], r2['companyTotalCurrentLiablities'],
                r1['companyTotalEquities'], r1['revenue'],
                r2['companyRetainedEarningsAccumulatedLoss'], r2['ebit'],
                r1['profitLossBeforeTaxFromContinuingOperations'], r1['profitLossAfterTaxFromContinuingOperations']]

    # Adding this line to csv file

    # Converting it to a string first
    temp_string = ','.join([str(item) for item in line]) + ','
    print(temp_string)

    # Editing Permanent DB
    with open(r'(Permanent) Smoothwork Company Database.csv', 'a', newline='\n') as f:
        f.write(temp_string + '\n')

    # Editing Weekly DB
    with open(r'(Weekly) Smoothwork Company Database.csv', 'a', newline='\n') as f:
        f.write(temp_string + '\n')

    pass


def query(company_and_date):
    # Separate Name and Date first
    company = company_and_date[0:10]
    temp_date = company_and_date[10:]
    date = reformat_date_to_yyyy_mm_dd(temp_date)

    # Two calls will be used. One for CoBrief 1 and CoBrief 2
    file = read_json('config.json')

    # Updating list of UENs Queried to prevent repeat calls
    if company_and_date in file['list']:
        print(company + ' information for the year ending ' + date + ' has been queried before')
        return
    else:
        file['list'] = file['list'] + ',' + company_and_date
        write_json_file('config.json', file)
        # print('commented out')

    # Setting variables
    fye = date
    payload = {
        'uen': company,
        'fyeDate': fye
    }

    header = {
        'token': file['accessToken']
    }

    # CoBrief 1
    brief1_url = 'https://www.apimall.acra.gov.sg/api/acra/financialInformationQuery/coBriefFinancials1'
    r = requests.get(brief1_url,
                     params=payload,
                     headers=header)

    if r.status_code == 200:
        print('Success fetching ' + company + ' details')
    else:
        print('Error fetching ' + company + ' details')

    # CoBrief 3
    brief2_url = 'https://www.apimall.acra.gov.sg/api/acra/financialInformationQuery/coBriefFinancials3'
    r2 = requests.get(brief2_url,
                      params=payload,
                      headers=header)

    if r.status_code == 200:
        print('Success fetching ' + company + ' details')
    else:
        print('Error fetching ' + company + ' details')

    # Once both responses are prepared, call add_to_CSV file

    # UNCOMMENT NEXT 3 LINES to test with coBrief1 and coBrief3.json
    # file1 = read_json('coBrief1.json')
    # file2 = read_json('coBrief3.json')
    # add_to_csv(file1, file2)

    add_to_csv(r.json(), r2.json())


def main():
    # Check if excel files are open.
    try:
        with open(r'(Permanent) Smoothwork Company Database.csv', 'a') as f:
            f.close()

        # Editing Weekly DB
        with open(r'(Weekly) Smoothwork Company Database.csv', 'a') as f:
            f.close()
    except:
        print('Close Excel Files and Try Again.')
        exit()

    # weekly needs to be cleansed before starting
    with open('(Weekly) Smoothwork Company Database.csv', 'w+', newline='\n') as f:
        f.write('UEN,Name,FYE Date,Total Assets,Total Current Assets,Total Liabilities,Total Current Liabilities,'
                'Total Equities,Revenue,Retained Earnings Accumulated Loss,EBIT,'
                'PLBeforeTaxFromContinuingOperations,PLAfterTaxFromContinuingOperations,\n')

    # Intiate Login
    login()

    # Read PASTEHERE.json file
    file = read_json('PASTEHERE.json')

    # Add all the companies to search to one complete list.
    list_of_companies_to_query = []
    for company in file:
        if company['Companies to Search For'] != "":
            temp_list = company['Companies to Search For'].split(' , ')
            for x in temp_list:
                list_of_companies_to_query.append(x)

    # Start querying each company
    for company in list_of_companies_to_query:
        query(company)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
