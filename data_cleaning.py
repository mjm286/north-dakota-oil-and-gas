import pandas as pd
import glob
import time
import re

t0 = time.time()
print('start')

county_abbv = {
    "BIL":"Billings",
    "BOT":"Bottineau",
    "BOW":"Bowman",
    "BRK":"Burke",
    "DIV":"Divide",
    "DUN":"Dunn",
    "GV":"Golden Valley",
    "MCH":"McHenry",
    "MCK":"McKenzie",
    "MCL":"McLean",
    "MTL":"Mountrail",
    "REN":"Renville",
    "SLP":"Slope",
    "STK":"Stark",
    "WRD":"Ward",
    "WIL":"Williams"
}
days_in_month = {
    "01":31,
    "02":28,
    "03":31,
    "04":30,
    "05":31,
    "06":30,
    "07":31,
    "08":31,
    "09":30,
    "10":31,
    "11":30,
    "12":31
}

oil = pd.concat(
    map(pd.read_excel, glob.glob("well_data/20*.xlsx"))
)

oil.columns = [name.lower() for name in oil.columns]

oil["company"] = oil['company'].str.replace(',',"", regex=False)
oil["company"] = oil['company'].str.replace('.',"", regex=False)
oil['county_name'] = oil['county'].map(county_abbv)

# format date
oil['reportdate'] = pd.to_datetime(oil['reportdate'])
oil["year"] = [x.strftime("%Y") for x in  oil["reportdate"]]
oil["month"] = [x.strftime("%m") for x in  oil["reportdate"]]
oil['days_in_month'] = oil['month'].map(days_in_month)
oil["reportdate"]=[str(x)[:-12] for x in oil["reportdate"]]

# company M&A
oil["company"] =oil['company'].str.replace('WPX ENERGY WILLISTON LLC',"DEVON ENERGY", regex=False)
oil["company"] =oil['company'].str.replace('XTO ENERGY INC',"EXXONMOBIL", regex=False)
oil["company"] =oil['company'].str.replace('BURLINGTON RESOURCES OIL & GAS COMPANY LP',"CONOCOPHILLIPS", regex=False)
oil["company"] =oil['company'].str.replace('OASIS PETROLEUM NORTH AMERICA LLC',"CHORD ENERGY", regex=False)
oil["company"] =oil['company'].str.replace('WHITING OIL AND GAS CORPORATION',"CHORD ENERGY", regex=False)

#metrics
oil['oil_per_day'] = oil['oil']/oil['days_in_month']
oil['gas_per_day'] = oil['gas']/oil['days_in_month']
oil['water_per_day'] = oil['wtr']/oil['days_in_month']
oil['gassold_per_day'] = oil['gassold']/oil['days_in_month']
oil['flared_per_day'] = oil['flared']/oil['days_in_month']
oil['gas_boe'] = oil['gas']/6
oil['gas_boe_per_day'] = oil['gas_per_day']/6
oil['total_boed'] = oil['gas_boe_per_day'] + oil['oil_per_day']

# oil[oil['oil_bbl_da'].isin([np.inf, -np.inf])].index

oil['reportdate'] = oil['reportdate'].astype('str')
oil['month'] = oil['month'].astype('int')
oil['year'] = oil['year'].astype('int')
oil['days_in_month'] = oil['days_in_month'].astype('int')

first_year = oil['year'].min()
last_year = oil["year"].max()

oil.to_pickle(f"North_Dakota_Well_Production_Data_{first_year}_{last_year}.pickle")
oil.to_csv(f"North_Dakota_Well_Production_Data_{first_year}_{last_year}.csv", index=False)

t1 = time.time()
total = (t1-t0)/60
print(f'total elapsed time: {total} minutes') # ~12 minutes
