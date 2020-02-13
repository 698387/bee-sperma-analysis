"""
Author: Pablo Luesia Lahoz
Date: February 2020
Description: Class for performance a spatial fuzzy c-means
"""

import numpy as np
import cv2 as cv
import random as r


class sFCM(object):
    """
    Init function.
    @param c is the number of clusters
    @param m controls the fuzzyness
    @param p is the parameter to power u
    @param q is the parameter to power h
    @param NB is the window size of the spatial part
    @param init_points are the optional initial points for the clusters 
    """
    def __init__(self, c=2, m = 2, p=1, q=1, NB = 3, init_points = np.array([])):
        self.c = c
        self.m = m
        self.p = p
        self.q = q
        self.NB = NB
        self.init_points = init_points
        r.seed()

    """
    Initialize the centroids based on the k-means++.
    @param image is the original data
    """
    def __init_centroids(self, data, data_shape):
        # The initial points are not defined by the user
        if len(self.init_points) == 0:

            # Flat the data for the point selection
            self.flat_data = data.reshape((data_shape[0]*data_shape[1], -1))
            idx_data = np.arange(self.flat_data.shape[0])

            # First centroid
            v = self.flat_data[np.random.choice(idx_data)]
            self.init_points = np.array([v])
            # Distance
            D = np.linalg.norm(self.flat_data - v, axis=1)

            # Select the rest of the centroids
            for i in range(1, self.c):
                D_max = max(D)
                # Probability depending on the distance
                p_aux = np.power(D,2) / D_max**2   
                # Normalized probability
                p = p_aux / sum(p_aux)                  
                # Select a next centroid
                v = self.flat_data[np.random.choice(idx_data, p = p)]   
                self.init_points = np.concatenate((self.init_points, [v]))
                # Compute distance
                D_aux = np.linalg.norm(self.flat_data - v, axis=1)
                D = np.array([D, D_aux]).min(axis = 0)

        return self.init_points

    """
    Returns the membership value of the data in data
    """
    def __get_membership(self, data, data_shape):
        # Diference between the centroid and the point
        v_dist = np.linalg.norm(
            np.repeat(
                np.expand_dims(data, axis = -1), 
                self.c, axis = -1)\
                    - self.v, axis = -1)
        # Repeated values for calculations
        v_dist_r =  np.repeat(
            np.expand_dims(v_dist, axis = -1),
            self.c, axis = -1)
        # Returns 1/(sum_(j=1)^(c)(v_dist_i/v_dist_j)^(2/(m-1)))
        # Nan values are converted to 1
        return np.nan_to_num( 1 / np.power(
            np.divide(v_dist_r,
                      v_dist_r.transpose((0,1,3,2))),
            2 / (self.m - 1)).sum(axis = -1), nan = 1.0)

    """
    Calculate the membership, depending on the spatial information
    """
    def __spatial_membership(self, data_shape, kernel, u):
        h = cv.filter2D(u, cv.CV_32F, kernel)
        up_hq = np.power(u, self.p) * np.power(h, self.q)
        return up_hq / up_hq.sum(axis=-1)\
            .reshape((data_shape[0], data_shape[1],1))

    """
    Update the centroids v with the new values
    """
    def __update_centroids(self, data, data_shape, u):
        flat_u =  u.reshape((data_shape[0]*data_shape[1], -1))
        return np.matmul(flat_u.transpose(), self.flat_data) \
            .reshape((self.c, -1)) \
           /flat_u.sum(axis = 0).reshape((self.c, -1))

    """
    Fit the cluster to the data
    @param data is a data representation. It has to be a 2d vector
    """
    def fit(self, raw_data, spatial = True):
        kernel = np.ones((self.NB, self.NB))
        # Data information extraction
        data_shape = raw_data.shape
        data = raw_data.astype(np.float32)
        # Sets the data to 3d
        if len(data_shape) < 3:                
            data = np.expand_dims(raw_data, axis=-1).astype(np.float32)
            data_shape = data.shape
            if len(data_shape) < 3:             # Checks the shape of the data
                raise TypeError("The data has to be 2d or 3d")

        # Initial centroids
        self.v = self.__init_centroids(data, data_shape)
        # Difference between old and new centroids
        diff_v = np.inf
        # Iterate until converges
        while diff_v > 0.05:
            # Membership values
            u = self.__get_membership(data, data_shape)
            if spatial:     # Extracts the spatial information if indicated
                u = self.__spatial_membership(data_shape, kernel, u)
            # New centroids
            v_n = self.__update_centroids(data, data_shape, u)
            # Convergence distance
            diff_v = max(np.linalg.norm(v_n - self.v, axis = 1))
            self.v = v_n

    """
    Predict the class asociated to each data in raw_data
    """
    def predict(self, raw_data, spatial = True):
        kernel = np.ones((self.NB, self.NB))
        # Data information extraction
        data_shape = raw_data.shape
        data = raw_data.astype(np.float32)
        # Sets the data to 3d
        if len(data_shape) < 3:                
            data = np.expand_dims(raw_data, axis=-1).astype(np.float32)
            data_shape = data.shape
            if len(data_shape) < 3:             # Checks the shape of the data
                raise TypeError("The data has to be 2d or 3d")

        # Predict the centroids
        u = self.__get_membership(data, data_shape)
        if spatial:     # Extracts the spatial information if indicated
            u = self.__spatial_membership(data_shape, kernel, u)
        
        # Maximum value of u is the predicted value
        return u.argmax(axis = -1)

