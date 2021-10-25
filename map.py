import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import shapely.geometry as geom

# add comment more comments

# read in hydrogen pipeline data
h2p = gpd.read_file("tx_h2_pipelines/tx_h2_pipelines.shp")

# read in EIA data
e860_file = pd.ExcelFile('eia860_plant_2020.xlsx')
e860 = pd.read_excel(e860_file, 'Sheet1')

e860 = e860.loc[e860['State'] == "TX"]
e860 = e860[['Plant Code', 'Latitude', 'Longitude']]
e860 = e860.drop_duplicates()

e923_file = pd.ExcelFile('eia923_2020.xlsx')
e923 = pd.read_excel(e923_file, 'Sheet1')

e923 = e923.loc[e923['Plant State'] == "TX"]
e923 = e923.loc[e923['Reported\nFuel Type Code'] == "NG"]

# e923.head()

e923 = e923[['Plant Id', 'Total Fuel Consumption\nMMBtu', 'Net Generation\n(Megawatthours)']]
e923 = e923.rename(columns={"Plant Id": "Plant Code", "Total Fuel Consumption\nMMBtu": "MMBTU_net", "Net Generation\n(Megawatthours)": "MWh_net"})

e923 = e923.groupby(['Plant Code']).sum()

# merge EIA data together
pp_data = e923.merge(e860, left_on='Plant Code', right_on='Plant Code')

# convert CSV with lat/long values to a geopandas GeoDataFrame
pp_data = gpd.GeoDataFrame(
    pp_data,
    geometry = gpd.points_from_xy(pp_data.Longitude, pp_data.Latitude),
    crs = 'epsg:4267')

# convert coordinates to meters
h2p = h2p.to_crs('epsg:32139')  # https://epsg.io/32139
pp_data = pp_data.to_crs('epsg:32139')


## add column in powerplants with distance to tx_h2_pipelines in meters cause CRS above
min_dist = np.empty(pp_data['Plant Code'].count())
for i, point in enumerate(pp_data['geometry']):
    min_dist[i] = np.min([point.distance(line) for line in h2p['geometry']])
pp_data['min_dist_to_lines'] = min_dist
pp_data.head(3)

# get NG power plants that are within 5k of h2 pipelines
near_plants_5k = pp_data[pp_data['min_dist_to_lines'] <= 5000]
near_plants_10k = pp_data[pp_data['min_dist_to_lines'] <= 10000]

# convert back to degrees
h2p = h2p.to_crs('epsg:4267')
near_plants_5k = near_plants_5k.to_crs('epsg:4267')
near_plants_10k = near_plants_10k.to_crs('epsg:4267')

# read in county GIS data
county = gpd.read_file("county_simple/county_simple.shp")
tx = county.loc[county['stt_bbr']=="TX"]
tx = tx.to_crs('epsg:4267')

# add point to dataframe to plot county name lable to in plot
tx['coords'] = tx['geometry'].apply(lambda x: x.representative_point().coords[:])
tx['coords'] = [coords[0] for coords in tx['coords']]


# plot figure
fig, ax = plt.subplots(figsize=(10, 10))
tx.plot(ax=ax, color="white", edgecolor="black")
h2p.plot(ax=ax, alpha=0.7, color="#e76f51", linewidth=2)
near_plants_5k.plot(ax=ax, color="#2a9d8f")


plt.xlim([-96, -93.5])
plt.ylim([28.75, 30.25])



for idx, row in tx.iterrows():
    plt.annotate(text=row['NAME'], xy=row['coords'],
                 horizontalalignment='center')

plt.savefig('h2_coast_plants.png', transparent=False)

## update to include 860 code to bring in capacity numbers, etc. merge on fuel, prime mover, etc.

e860_file_all = pd.ExcelFile('eia860_2020.xlsx')
e860_all = pd.read_excel(e860_file_all, 'Sheet1')
plants_5k = e860_all.loc[e860_all['Plant Code'].isin(near_plants_5k['Plant Code'])]
plants_10k = e860_all.loc[e860_all['Plant Code'].isin(near_plants_10k['Plant Code'])]

plants_5k.to_csv(r'plants_5k.csv')
plants_10k.to_csv(r'plants_10k.csv')

near_plants_5k.to_csv(r'plants_5k_gen.csv')
near_plants_10k.to_csv(r'plants_10k_gen.csv')


######## scratch
# near_plants_5k

# make shapefile
# near_plants_5k.to_file("plants_5k_spatial/plants_5k.shp")
