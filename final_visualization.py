"""
Author: Heather Koo

Mia Skinner
Heather Koo
CIS41B Final project
final_visualization.py:
- reads data from the product order database, and find the best model for each product by using polynomial regression.
  It predicts the future quantity of the product based on given condition, and visualize it by plotting graph.
"""

import sqlite3
import collections
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn import metrics
import threading

MIN_DATA_PTS = 10  # minimum number of data for modeling.
MIN_R2 = 0.20      # minimum R2 value to predict the future data.

class PlotOrder(object):
    """
    reads data from the product order database, and find the best model for each product by using polynomial regression.
    It predicts the future quantity of the product based on given condition, and visualize it by plotting graph.
    """
    def __init__(self):
        """
        reads data from the product order database, and create a dictionary for modelling.
        """
        self._readData()
        self._createModelDict()


    def _readData(self):
        """
        reads data from the product order database.
        :return: None
        """
        self.conn = sqlite3.connect('Shipments.db')
        self.cur = self.conn.cursor()

    def _createOrderDict(self):
        """
        create a dictionary called 'self.productOrderDB_cal' from the database,
        with key: product ID, value: dictionary(key: calendar year, value: dictionary(key: month, value: quantity))
        :return: None
        """
        self.productOrderDB_cal = dict()
        # create a dictionary whose key is the product ID and value is the default dictionary.
        for record in self.cur.execute('''SELECT mkt_item_wid, cust_ship_date, quantity FROM Shipments'''):
            self.productOrderDB_cal[record[0]] = collections.defaultdict(dict)

        # insert the calendar year of each product order into the key of the default dictionary
        # and create another default dictionary.
        for record in self.cur.execute('''SELECT mkt_item_wid, cust_ship_date, quantity FROM Shipments'''):
            # skip 2050 year in the database
            if not int(record[1].split('-')[0]) == 2050:
                self.productOrderDB_cal[record[0]][int(record[1].split('-')[0])] = collections.defaultdict(float)

        # fill every month into the default dictionary and initialize the quantity as zero by default.
        # because the database contains only positive value of product quantity.
        for k, v in self.productOrderDB_cal.items():
            for year, d in v.items():
                for i in range(1, 13):
                    d[i] = 0

        # add all product quantities for each month.
        for record in self.cur.execute('''SELECT mkt_item_wid, cust_ship_date, quantity FROM Shipments'''):
            if not int(record[1].split('-')[0]) == 2050:
                self.productOrderDB_cal[record[0]][int(record[1].split('-')[0])][int(record[1].split('-')[1])] += record[2]


    def _createModelDict(self):
        """
        create a dictionary called 'self.modelDict' from the productOrderDB_cal dictionary,
        with key: product ID, value: a list of quantities in order of months including zero quantities.
        :return: None
        """
        self._createOrderDict()
        self.modelDict = collections.defaultdict(list)

        for k, v in self.productOrderDB_cal.items():
            for year, dic in sorted(v.items()):
                for m, q in sorted(dic.items()):
                    self.modelDict[k].append(q)
        #print(self.modelDict)


    def findAvaliableProducts(self):
        """
        a generator that generates product ID who has enough number of data to create a model.
        The list of products will appear in the listbox option.
        :return: None
        """
        for i, qList in self.modelDict.items():
            arr = np.array(qList)
            if len(arr[arr>0]) > MIN_DATA_PTS:
                yield i


    def modeling(self, productID):
        """
        find the best model for the given product ID by using polynomial regression.
        :param productID:
        :return maxR2:
        """
        monthList = []        # non zero quantity list
        quantityList = []     # corresponding month list

        for i in range(len(self.modelDict[productID])):
            if self.modelDict[productID][i] != 0:
                monthList.append(i+1)
                quantityList.append(self.modelDict[productID][i])

        if len(monthList) > MIN_DATA_PTS:
            # x, y is the original data-set for modeling.
            x = np.array(monthList)
            y = np.array(quantityList)

            self.x_forPlot = x[:, np.newaxis]
            y_forPlot = y[:, np.newaxis]

            df = pd.DataFrame(data=np.concatenate((np.transpose(x[np.newaxis]), np.transpose(y[np.newaxis])), axis=1),
                              columns=['X', 'y'])

            X = df['X'][:, np.newaxis]
            y = df['y']

            # Train test split to avoid overfitting
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

            # Use multi-threading to gather the metrics data with the degrees 2~9
            self.metricsDict = collections.defaultdict(float)
            threads = []
            for degree in range(2, 9):
                t = threading.Thread(target=self.findBestDegree, args=(X_train, X_test, y_train, y_test, degree))
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            # find the best degree by finding maximum r2_test
            self.bestDegree = 2
            maxR2 = self.metricsDict[self.bestDegree][3]
            for k, v in self.metricsDict.items():
                if v[3] > maxR2:
                    self.bestDegree = k
                    maxR2 = v[3]

            # find a model with the best degree based on the original data-set for plotting.
            self.polynomial_features = PolynomialFeatures(degree=self.bestDegree)
            x_poly = self.polynomial_features.fit_transform(self.x_forPlot)

            self.model = LinearRegression()
            self.model.fit(x_poly, y_forPlot)

            self.y_poly_pred = self.model.predict(x_poly)

            return maxR2


    def findBestDegree(self, X_train, X_test, y_train, y_test, degreeNum=3):
        """
        stores the evaluating information of the polynomial regression model for a given degree number.
        uses random training data to avoid overfitting.
        :param X_train, X_test, y_train, y_test, degreeNum
        :return: None
        """

        poly_features = PolynomialFeatures(degree=degreeNum)

        # transforms the existing features to higher degree features.
        X_train_poly = poly_features.fit_transform(X_train)

        # fit the transformed features to Linear Regression
        poly_model = LinearRegression()
        poly_model.fit(X_train_poly, y_train)

        # predicting on training data-set
        y_train_predicted = poly_model.predict(X_train_poly)

        # predicting on test data-set
        y_test_predict = poly_model.predict(poly_features.fit_transform(X_test))

        # evaluating the model on training dataset
        rmse_train = np.sqrt(metrics.mean_squared_error(y_train, y_train_predicted))
        r2_train = metrics.r2_score(y_train, y_train_predicted)

        # evaluating the model on test dataset
        rmse_test = np.sqrt(metrics.mean_squared_error(y_test, y_test_predict))
        r2_test = metrics.r2_score(y_test, y_test_predict)
        mae_test = metrics.mean_absolute_error(y_test, y_test_predict)

        self.metricsDict[degreeNum] = (rmse_train, r2_train, rmse_test, r2_test, mae_test)

    def getMae(self):
        """
        returns mean absolute error which represents accuracy of the model.
        :return: mae value
        """
        return self.metricsDict[self.bestDegree][4]


    def forecastPlot(self, productID, m, startYear, startMon):
        """
        plots the forecast data with previous trend for given user choice - product ID, duration, starting date.
        :param productID, m, startYear, startMon
        :return: a tuple of data for plotting
        """
        if m == 0: m = 1        # One month choice
        elif m == 1: m = 3      # One quarter choice
        elif m == 2: m = 12     # One year choice

        maxR2 = self.modeling(productID)
        # find the index of the start month.
        currX = (startYear - sorted(self.productOrderDB_cal[productID].keys())[0])*12+startMon

        monForPredictoin = []
        for i in range(m):
            monForPredictoin.append(currX + i + 1)

        currX_forPlot = np.array(monForPredictoin)[:, np.newaxis]
        currX_plot = self.polynomial_features.fit_transform(currX_forPlot)

        # predicted y values from the model
        forecastY = self.model.predict(currX_plot)
        xticks1 = list(range(1, len(self.modelDict[productID]) + 1))

        for f in forecastY:
            if f[0] < 0:
                #print("The quantity value is negative")
                f[0] = 0.05     # to show the zero value on the graph as a short stub

            # for the unrealistic modeling case where R2 value is negative and mae is greater than 100,
            # set the result as zero.
            if maxR2 < MIN_R2 and self.getMae() > 100:
                self.modelDict[productID].append(0)
                #print("R2 value of the model is", maxR2)
                #print("MAE value of the model is", self.getMae())
            else: self.modelDict[productID].append(f[0])

        # x axis for the graph
        xticks1.extend(monForPredictoin)

        # Bar chart
        barList=plt.bar(xticks1, self.modelDict[productID])
        for i in range(1, m+1):
            barList[-1*i].set_color('r')    # for the forecast data, bar color is red

        newXticks = []
        for i in xticks1:
            i %= 12
            if i == 0: i = 12
            newXticks.append(i)

        # label months as the first x axis
        plt.xticks(xticks1, newXticks)
        plt.title("Product " + str(productID) + " Forecast")
        plt.ylabel("Quantity")
        plt.ylim(bottom=0)
        ax1 = plt.subplot(1,1,1)
        ax1.set_xlabel('Months')
        # double x axis to show both month and year
        ax2 = ax1.twiny()
        newlabel = [year for year in self.productOrderDB_cal[productID].keys() if year <= startYear]
        if m == 12: startYear += 1
        if startYear not in newlabel:
            year = newlabel[-1] + 1
            while startYear >= year:
                newlabel.append(year)
                year += 1

        newpos = []
        n = 8
        for i in range(len(newlabel)):
            newpos.append(n)
            n += 12
        ax2.set_xticks(newpos)
        ax2.set_xticklabels(newlabel)
        ax2.xaxis.set_ticks_position('bottom')  # set the position of the second x-axis to bottom
        ax2.xaxis.set_label_position('bottom')  # set the position of the second x-axis to bottom
        ax2.spines['bottom'].set_position(('outward', 36))
        ax2.set_xlabel('Years')
        ax2.set_xlim(ax1.get_xlim())

        # plot the model graph
        plt.plot(self.x_forPlot, self.y_poly_pred, color='m')

        return self.x_forPlot, self.y_poly_pred, m, xticks1, self.modelDict[productID], newlabel, newpos


    def savedForecastPlot(self, x, y, m, productID, listX, listY, newlabel, newpos):
        """
        plots the graph from the saved data when user clicks the listbox.
        :param x, y, m, productID, listX, listY, newlabel, newpos
        :return: None
        """
        barList = plt.bar(listX, listY)

        for i in range(1, m + 1):
            barList[-1 * i].set_color('r')

        newXticks = []
        for i in listX:
            i %= 12
            if i == 0: i = 12
            newXticks.append(i)

        plt.xticks(listX, newXticks)
        plt.title("Product " + str(productID) + " Forecast")
        plt.ylabel("Quantity")
        plt.ylim(bottom=0)
        ax1 = plt.subplot(1, 1, 1)
        ax1.set_xlabel('Months')
        ax2 = ax1.twiny()

        ax2.set_xticks(newpos)
        ax2.set_xticklabels(newlabel)
        ax2.xaxis.set_ticks_position('bottom')  # set the position of the second x-axis to bottom
        ax2.xaxis.set_label_position('bottom')  # set the position of the second x-axis to bottom
        ax2.spines['bottom'].set_position(('outward', 36))
        ax2.set_xlabel('Years')
        ax2.set_xlim(ax1.get_xlim())

        plt.plot(x, y, color='m')



#p = PlotOrder()
