# from https://github.com/burtonrj/consensusclustering/

from __future__ import annotations

from itertools import combinations
from typing import Type
from warnings import warn

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from joblib import Parallel, delayed
from .kneed import KneeLocator
from tqdm.auto import tqdm

def resample(x: np.ndarray, frac: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Resample a matrix x by a fraction frac

    Parameters
    ----------
    x: np.ndarray
        Matrix to resample
    frac: float
        Fraction of rows to resample

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Indices of resampled rows and resampled matrix
    """
    resampled_indices = np.random.choice(
        range(x.shape[0]), size=int(x.shape[0] * frac), replace=False
    )
    return resampled_indices, x[resampled_indices, :]


def compute_connectivity_matrix(labels: np.ndarray) -> np.ndarray:
    """
    Compute a connectivity matrix from a vector of labels - the connectivity matrix
    is a symmetric matrix where the (i, j)th entry is 1 if the ith and jth elements
    of the labels vector are the same and 0 otherwise.

    Computation of connectivity matrices handles out-of-bag samples by setting the
    (i, j)th entry to 0 if either the ith or jth element of the labels vector is -1,
    where a -1 indicates the item is not included in the sample. IF YOU ARE USING
    A CLUSTERING ALGORITHM THAT DESIGNATES LABELS AS -1, YOU MUST CHANGE THE LABELS
    TO A DIFFERENT VALUE BEFORE CALLING THIS FUNCTION.

    Parameters
    ----------
    labels: np.ndarray
        Vector of labels

    Returns
    -------
    np.ndarray
        Connectivity matrix
    """
    out_of_bag_idx = np.where(labels == -1)[0]
    connectivity_matrix = np.equal.outer(labels, labels).astype("int8")
    rows, cols = zip(*list(combinations(out_of_bag_idx, 2)))
    connectivity_matrix[rows, cols] = 0
    connectivity_matrix[cols, rows] = 0
    connectivity_matrix[out_of_bag_idx, out_of_bag_idx] = 0
    return connectivity_matrix


def compute_identity_matrix(x: np.ndarray, resampled_indices: np.ndarray) -> np.ndarray:
    """
    Compute an identity matrix from a matrix x and a vector of resampled indices - the
    identity matrix is a symmetric matrix where the (i, j)th entry is 1 if the ith and
    jth elements are both in the resampled indices and 0 otherwise.

    Parameters
    ----------
    x: np.ndarray
        Matrix that was resampled
    resampled_indices: np.ndarray
        Indices of resampled rows

    Returns
    -------
    np.ndarray
        Identity matrix
    """
    n = x.shape[0]
    identity_matrix = np.zeros((n, n), dtype="int8")
    rows, cols = zip(*list(combinations(resampled_indices, 2)))
    identity_matrix[rows, cols] = 1
    identity_matrix[cols, rows] = 1
    identity_matrix[resampled_indices, resampled_indices] = 1
    return identity_matrix


def compute_consensus_matrix(
    connectivity_matrices: list[np.ndarray], identity_matrices: list[np.ndarray]
) -> np.ndarray:
    """
    Compute a consensus matrix from a list of connectivity matrices and a list of
    identity matrices - the consensus matrix is a symmetric matrix where the (i, j)th
    entry is the proportion of connectivity matrices where the ith and jth elements
    are connected normalized by the proportion of identity matrices where the ith and
    jth elements are sampled.

    Parameters
    ----------
    connectivity_matrices: list[np.ndarray]
        List of connectivity matrices
    identity_matrices: list[np.ndarray]
        List of identity matrices

    Returns
    -------
    np.ndarray
        Consensus matrix
    """
    return np.nan_to_num(
        np.sum(connectivity_matrices, axis=0) / np.sum(identity_matrices, axis=0), nan=0
    )


def valid_clustering_obj(clustering_obj, k_param: str) -> bool:
    """
    Check if a clustering object has the necessary methods to be used in consensus
    clustering (i.e. Scikit-learn signatures)

    Parameters
    ----------
    clustering_obj: object
        Clustering object to check
    k_param: str
        Name of the parameter that sets the number of clusters

    Returns
    -------
    bool
        True if clustering_obj has fit_predict and set_params methods,
        False otherwise.
    """
    if not hasattr(clustering_obj, "fit_predict"):
        return False
    if not hasattr(clustering_obj, "set_params"):
        return False
    if not hasattr(clustering_obj, k_param):
        return False
    return True


def cluster(
    x: np.ndarray,
    resample_frac: float,
    k: int,
    clustering_obj,
    k_param: str = "n_clusters",
) -> tuple[Type, np.ndarray, np.ndarray]:
    """
    Sample a matrix x and cluster the resampled matrix, returning the clustering
    object, the indices of the resampled rows, and labels for the items in x with
    a value of -1 for items not included in the resampled matrix.

    Parameters
    ----------
    x: np.ndarray
        Matrix to resample and cluster
    resample_frac: float
        Fraction of rows to resample
    k: int
        Number of clusters
    clustering_obj
        Clustering object to use; must have fit_predict and set_params methods
    k_param: str
        Name of the parameter that sets the number of clusters

    Returns
    -------
    tuple[Type, np.ndarray, np.ndarray]
        Clustering object, indices of resampled rows, and labels for the items in x
    """
    if not valid_clustering_obj(clustering_obj, k_param):
        raise ValueError("clustering_obj must have fit_predict and set_params methods")
    clustering_obj.set_params(**{k_param: k})
    resampled_indices, resampled_x = resample(x, resample_frac)
    resampled_labels = clustering_obj.fit_predict(resampled_x)

    if -1 in resampled_labels:
        raise ValueError(
            "Clustering object returned -1 as a label. -1 is reserved for items not "
            "included in the resampled matrix. Please modify the clustering object "
            "to return a label other than -1."
        )

    labels = np.full(x.shape[0], -1)
    labels[resampled_indices] = resampled_labels
    return clustering_obj, resampled_indices, labels


class ConsensusClustering:
    """
    Consensus clustering for measuring the stability of clusters and selecting the
    optimal number of clusters. Consensus clustering is originally described in
    https://link.springer.com/article/10.1023/A:1023949509487 and implemented in R
    in the ConsensusClusterPlus package (https://academic.oup.com/bioinformatics/article/26/12/1572/281699). 
    This class is a Python implementation of the same algorithm.

    Clustering stability is measured by resampling rows of a matrix, clustering the
    resampled matrix, and computing a consensus matrix from the resampled clusters.
    The consensus distribution of each pair of items is used to measure cluster
    stability and the optimal number of clusters chosen by maximizing the change
    in the area under the cumulative distribution function (CDF) of the consensus
    matrix.
    """

    def __init__(
        self,
        clustering_obj,
        min_clusters: int,
        max_clusters: int,
        n_resamples: int,
        resample_frac: float = 0.5,
        k_param: str = "n_clusters",
    ):
        """
        Initialize a ConsensusClustering object.

        Parameters
        ----------
        clustering_obj
            Clustering object to use; must have fit_predict and set_params methods.
        min_clusters: int
            Minimum number of clusters to consider. Must be greater than or equal to 2.
        max_clusters: int
            Maximum number of clusters to consider.
        n_resamples: int
            Number of resamples to perform.
        resample_frac: float
            Fraction of rows to resample.
        k_param: str
            Name of the parameter that sets the number of clusters.
        """
        self.clustering_obj = clustering_obj
        self.min_clusters = min_clusters
        self.max_clusters = max_clusters
        self.n_resamples = n_resamples
        self.resample_frac = resample_frac
        self.consensus_matrices_: list[np.ndarray] = []
        self.k_param = k_param

        if self.min_clusters < 2:
            raise ValueError("min_clusters must be >= 2")
        if self.max_clusters < self.min_clusters:
            raise ValueError("max_clusters must be >= min_clusters")

    @property
    def cluster_range_(self) -> list[int]:
        return list(range(self.min_clusters, self.max_clusters + 1))

    def consensus_k(self, k: int) -> np.ndarray:
        """
        Get the consensus matrix for a given number of clusters.

        Parameters
        ----------
        k: int
            Number of clusters

        Returns
        -------
        np.ndarray
            Consensus matrix for k
        """
        if len(self.consensus_matrices_) == 0:
            raise ValueError("Consensus matrices not computed yet.")
        return self.consensus_matrices_[k - self.min_clusters]

    def _fit_multiprocess(
        self, x: np.ndarray, progress_bar: bool = False, n_jobs: int = -1
    ):
        """
        Compute consensus matrices for all values of k in parallel

        Parameters
        ----------
        x: np.ndarray
            Matrix to cluster
        progress_bar: bool (default: False)
            Whether to display a progress bar
        n_jobs: int (default: -1)
            Number of jobs to run in parallel

        Returns
        -------
        None
            Consensus matrices are stored in self.consensus_matrices_
        """
        self.consensus_matrices_ = []
        with Parallel(n_jobs) as parallel:
            self.consensus_matrices_ = list(
                parallel(
                    delayed(self._fit_single_k)(x, k)
                    for k in tqdm(
                        self.cluster_range_,
                        disable=not progress_bar,
                        desc="Computing consensus matrices",
                        total=self.max_clusters - self.min_clusters + 1,
                    )
                )
            )

    def _fit_single_k(self, x: np.ndarray, k: int) -> np.ndarray:
        """
        Compute the consensus matrix for a single value of k.

        Parameters
        ----------
        x: np.ndarray
            Matrix to cluster
        k: int
            Number of clusters

        Returns
        -------
        np.ndarray
            Consensus matrix for k
        """
        connectivity_matrices = []
        identity_matrices = []
        for _ in range(self.n_resamples):
            _, resampled_indices, labels = cluster(
                x, self.resample_frac, k, self.clustering_obj, self.k_param
            )
            connectivity_matrices.append(compute_connectivity_matrix(labels))
            identity_matrices.append(compute_identity_matrix(x, resampled_indices))
        return compute_consensus_matrix(connectivity_matrices, identity_matrices)

    def fit(self, x: np.ndarray, progress_bar: bool = False, n_jobs: int = 0) -> None:
        """
        Compute consensus matrices for all values of k.

        Parameters
        ----------
        x: np.ndarray
            Matrix to cluster
        progress_bar: bool (default: False)
            Whether to display a progress bar
        n_jobs: int (default: 0)
            Number of jobs to run in parallel. If 0, run in serial.

        Returns
        -------
        None
            Consensus matrices are stored in ``self.consensus_matrices_``
            
        """
        self.consensus_matrices_ = []
        if n_jobs == 0:
            for k in tqdm(
                self.cluster_range_,
                disable=not progress_bar,
                desc="Computing consensus matrices",
                total=self.max_clusters - self.min_clusters + 1,
            ):
                self.consensus_matrices_.append(self._fit_single_k(x, k))
        else:
            self._fit_multiprocess(x, progress_bar, n_jobs)

    def hist(self, k: int) -> tuple[np.ndarray, np.ndarray]:
        """
        Compute the histogram of the consensus matrix for a given number of clusters.

        Parameters
        ----------
        k: int
            Number of clusters

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            Histogram and bins
        """
        hist, bins = np.histogram(self.consensus_k(k).ravel(), density=True)
        return hist, bins

    def cdf(self, k: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute the cumulative distribution function (CDF) of the consensus matrix for
        a given number of clusters.

        Parameters
        ----------
        k: int
            Number of clusters

        Returns
        -------
        tuple[np.ndarray, np.ndarray, np.ndarray]
            CDF, histogram, and bins
        """
        hist, bins = self.hist(k)
        ecdf = np.cumsum(hist)
        bin_widths = np.diff(bins)
        ecdf = ecdf * bin_widths
        return ecdf, hist, bins

    def area_under_cdf(self, k: int) -> float:
        """
        Compute the area under the cumulative distribution function (CDF) of the
        consensus matrix for a given number of clusters.

        Parameters
        ----------
        k: int
            Number of clusters

        Returns
        -------
        float
            Area under the CDF
        """
        ecdf, _, bins = self.cdf(k)
        return np.sum(ecdf * (bins[1:] - bins[:-1]))

    def change_in_area_under_cdf(self) -> np.ndarray:
        """
        Compute the proportional change in the area under the cumulative distribution
        function (CDF) of the consensus matrix for each number of clusters.

        Returns
        -------
        np.ndarray
            Proportional change in area under the CDF as a function of the number of
            clusters
        """
        auc = [self.area_under_cdf(k) for k in self.cluster_range_]
        delta_k = [
            (b - a) / b if k > 2 else a
            for a, b, k in zip(auc[:-1], auc[1:], self.cluster_range_)
        ]
        return np.array(delta_k)

    def best_k(self, method: str = "knee") -> int:
        """
        Compute the optimal number of clusters by maximizing the change in the area
        under the cumulative distribution function (CDF) of the consensus matrix.

        Returns
        -------
        int
            Optimal number of clusters
        """
        if method == "change_in_auc":
            change = self.change_in_area_under_cdf()
            largest_change_in_auc = np.argmax(change)
            return list(range(self.min_clusters, self.max_clusters))[
                largest_change_in_auc
            ]
        elif method == "knee":
            kneedle = KneeLocator(
                self.cluster_range_,
                [self.area_under_cdf(k) for k in self.cluster_range_],
                curve="concave",
                direction="increasing",
            )
            if kneedle.knee is None:
                warn(
                    "Kneedle algorithm failed to find a knee. "
                    "Returning maximum number of clusters, however, it is likely that "
                    "the clustering is unstable. Plot the CDFs and consensus matrices "
                    "to check."
                )
                return self.max_clusters
            return kneedle.knee
        else:
            raise ValueError("method must be one of 'change_in_auc' or 'knee'")

    def plot_auc_cdf(self, include_knee: bool = True, ax: plt.Axes | None = None):
        """
        Plot the area under the cumulative distribution function (CDF)
        of the consensus matrix as a function of the number of clusters.

        Parameters
        ----------
        include_knee: bool (default: True)
            Whether to include a vertical line at the knee
        ax: plt.Axes (default: None)
            Axis on which to plot

        Returns
        -------
        None
        """
        ax = plt.subplots(figsize=(5, 5))[1] if ax is None else ax
        auc = [self.area_under_cdf(k) for k in self.cluster_range_]
        ax.plot(
            self.cluster_range_,
            auc,
            "--",
            marker="o",
            markerfacecolor="white",
            markeredgecolor="black",
        )
        if include_knee:
            knee = self.best_k(method="knee")
            ax.axvline(
                knee,
                color="k",
                linestyle="--",
                label="Knee",
            )
        ax.set_xlabel("K")
        ax.set_ylabel("Area under CDF")
        return ax

    def plot_clustermap(self, k: int, **kwargs):
        """
        Plot a clustermap of the consensus matrix for a given number of clusters.

        Parameters
        ----------
        k: int
            Number of clusters
        kwargs:
            Keyword arguments to pass to seaborn.clustermap

        Returns
        -------
        seaborn.ClusterGrid
        """
        return sns.clustermap(self.consensus_k(k), **kwargs)

    def plot_hist(self, k: int, ax: plt.Axes | None = None) -> plt.Axes:
        """
        Plot a histogram of the consensus matrix for a given number of clusters.

        Parameters
        ----------
        k: int
            Number of clusters
        ax: plt.Axes | None
            Axis to plot on, or None to create a new figure

        Returns
        -------
        matplotlib.pyplot.Axes
        """
        ax = ax if ax is not None else plt.subplots(figsize=(6.5, 6.5))[1]
        hist, bins = self.hist(k)
        ax.bar(bins[:-1], hist, width=np.diff(bins))
        ax.set_xlabel("Consensus index value")
        ax.set_ylabel("Density")
        ax.set_xlim(0, 1)
        return ax

    def plot_cdf(self, ax: plt.Axes | None = None) -> plt.Axes:
        """
        Plot the cumulative distribution function (CDF) of the consensus matrix for
        each number of clusters.

        Parameters
        ----------
        ax: plt.Axes | None
            Axis to plot on, or None to create a new figure

        Returns
        -------
        matplotlib.pyplot.Axes
        """
        ax = ax if ax is not None else plt.subplots(figsize=(5, 5))[1]
        for k in self.cluster_range_:
            ecdf, _, bins = self.cdf(k)
            ax.step(bins[:-1], ecdf, label=f"{k} clusters")
        ax.set_xlabel("Consensus index value")
        ax.set_ylabel("CDF")
        ax.set_xlim(0, 1)
        ax.legend()
        return ax

    def plot_change_area_under_cdf(self, ax: plt.Axes | None = None) -> plt.Axes:
        """
        Plot the change in the area under the cumulative distribution function (CDF)
        of the consensus matrix for each number of clusters.

        Parameters
        ----------
        ax: plt.Axes | None
            Axis to plot on, or None to create a new figure

        Returns
        -------
        matplotlib.pyplot.Axes
        """
        ax = ax if ax is not None else plt.subplots(figsize=(5, 5))[1]
        change = self.change_in_area_under_cdf()
        ax.plot(
            self.cluster_range_[:-1],
            change,
            "--",
            marker="o",
            markerfacecolor="white",
            markeredgecolor="black",
        )
        ax.set_xlabel("K")
        ax.set_ylabel("Change in area under CDF")
        return ax