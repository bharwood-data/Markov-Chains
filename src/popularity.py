"""
popularity.py

This script implements functions to simulate popularity scenario simulations
and append results to shared lists. It introduces missing data unbiased on state
popularity, calculates RMSE, and appends results after each run.

Author: Ben Harwood
Contact: bharwood@syr.edu
Website: https://github.com/bharwood-data/Markov-Chains

Functions:
    introduce_popularity_bias: Introduces missing data unbiased on state popularity.
    popAppend: Appends popularity scenario results to shared lists.
    process_popularity: Runs popularity scenario simulations and appends results.

Dependencies:
    - pandas: A powerful data manipulation library.
    - numpy: A fundamental package for scientific computing with Python.
    - time: A module providing various time-related functions.
    - itertools: A module providing iterators for efficient looping.
    - random: A module providing functions for generating random numbers.

    - generate_standard_transition_matrix: Generates a standard transition matrix.
    - generate_initial_states: Generates initial states for multiple agents.
    - generate_markov_chains: Generates Markov chains for multiple agents.
    - extract_transition_matrix: Extracts a transition matrix from a DataFrame.
    - kl_divergence: Calculates the Kullback-Leibler divergence.
    - generate_random_prevalence_ratios: Generates random prevalence ratios.
    - construct_weighted_transition_matrix: Constructs a weighted transition matrix.
    - generate_custom_initial_distribution: Generates a custom initial distribution.
    - introduce_popularity_bias: Introduces popularity bias to data.
    - forward_algorithm: Performs forward algorithm for imputation.
    - em_algorithm: Performs EM algorithm for optimization.
"""

import pandas as pd
import numpy as np
import time as time
import itertools
import random

from bmcUtils import generate_standard_transition_matrix, generate_initial_states, generate_markov_chains, \
    extract_transition_matrix, kl_divergence, kl_divergence, generate_random_prevalence_ratios, construct_weighted_transition_matrix, \
    generate_custom_initial_distribution, introduce_popularity_bias
from bmcSpecial import forward_algorithm, em_algorithm

def introduce_popularity_bias(d1, state_probabilities, desired_missing_pct, N, T, asc):
    """
    Introduces missing data unbiasedd on state popularity.

    Processes data to introduce missing values unbiasedd on specified state probabilities.
    More popular states will have fewer missing values.

    Args:
        d1 (DataFrame): Original data.
        state_probabilities (DataFrame): DataFrame of state probabilities.
        desired_missing_pct (float): Desired percentage of missing values.
        N (int): Number of rows in data.
        T (int): Number of columns in data.
        asc (bool): Whether to sort states by probability in ascending order.

    Returns:
        DataFrame: Data with missing values introduced.
    """
    # Check if d1 and state_probabilities are DataFrames
    if not isinstance(d1, pd.DataFrame) or not isinstance(state_probabilities, pd.DataFrame):
        raise ValueError("d1 and state_probabilities must be pandas DataFrames")

    # Check if N and T are integers
    if not isinstance(N, int) or not isinstance(T, int):
        raise ValueError("N and T must be integers")

    # Check if desired_missing_pct is a float between 0 and 1
    if not isinstance(desired_missing_pct, float) or not 0 <= desired_missing_pct <= 1:
        raise ValueError("desired_missing_pct must be a float between 0 and 1")

    # Check if asc is a boolean
    if not isinstance(asc, bool):
        raise ValueError("asc must be a boolean")

    try:
        # Create a copy of the original data
        d2 = d1.iloc[:, 1:].copy()
        states = state_probabilities.shape[0]
        
        # Sort the states by probability
        sorted_states = state_probabilities.sort_values(by='Probability', ascending=asc)

        # Calculate the desired number of missing values
        desired_missing_count = round(desired_missing_pct * N * T)

        # Create a list to store state indices
        state_indices_list = [[] for _ in range(states)]

        # Store the indices of each state's observations
        for state in range(states):
            state_indices_list[state] = np.where(d1.values == state)

        # Initialize a variable to track the remaining missing count
        remaining_missing_count = desired_missing_count

        # Loop through the states in order of probability
        for i in range(len(sorted_states)):
            if remaining_missing_count <= 0:
                break
            state = sorted_states['State'].values[i]
            
            occurrences = (d2 == state).sum().sum()
            
            # Calculate the number of occurrences to mark as NaN
            needed = int(occurrences * 0.9)
            
            # Randomly generate observations for the current state
            if needed > 0:
                # Identify the indices of occurrences for the current state
                state_indices = np.where(d2.values == state)
                
                # Randomly select indices for the current state
                selected_indices = random.sample(list(zip(state_indices[0], state_indices[1])), k=needed)
                
                # Mark occurrences as NaN using the selected indices
                for index in selected_indices:
                    d2.iloc[index] = np.nan
                    # Update the remaining missing count
                    remaining_missing_count -= 1
                    if remaining_missing_count == 0:
                        break

        return d2
    except Exception as e:
        raise ValueError(f"An error occurred during popularity bias introduction: {e}")
    
def popAppend(states_list, states, missing_list, pct, time_list, standard_time, KL_list, KL, inaccuracy_list, p, agents_list, N, obs_list, 
              T, popularity_list, popularity, imputed_list=None, imputed=None, em_list=None, em=None, emTime_list=None, emTime=None, 
              imputed_time_list=None, imputedTime=None):
    """
    Appends popularity scenario results to shared lists.

    The function appends states, missing %, RMSE, agents,
    observations, and ascending order to their respective
    shared lists after each run.

    Args:
        states_list (list): Shared list to append states.
        states (int): Number of states.
        missing_list (list): Shared list to append missing percentage.
        pct (float): Percent missing data.
        time_list (list): Shared list to append execution time.
        standard_time (float): Time taken for execution.
        KL_list (list): Shared list to append KL divergence.
        KL (float): KL divergence.
        inaccuracy_list (list): Shared list to append inaccuracy.
        p (float): Inaccuracy.
        agents_list (list): Shared list to append number of agents.
        N (int): Number of agents.
        obs_list (list): Shared list to append number of observations.
        T (int): Number of observations.
        popularity_list (list): Shared list to append popularity.
        popularity (bool): Popularity order.
        imputed_list (list): Shared list to append imputation result (optional).
        imputed (float): Imputation result (optional).
        em_list (list): Shared list to append EM result (optional).
        em (float): EM result (optional).
        emTime_list (list): Shared list to append EM execution time (optional).
        emTime (float): EM execution time (optional).
        imputed_time_list (list): Shared list to append imputation execution time (optional).
        imputedTime (float): Imputation execution time (optional).

    Returns:
        tuple: Tuple of updated shared lists.
    """
    # Append states, missing %, execution time, KL divergence, inaccuracy, number of agents, number of observations, and popularity to respective lists
    states_list.append(states)
    missing_list.append(pct)
    time_list.append(standard_time)
    KL_list.append(KL)
    inaccuracy_list.append(p)
    popularity_list.append(popularity)
    agents_list.append(N)
    obs_list.append(T)
    # Append imputation result if available
    if imputed_list is not None:
        imputed_list.append(imputed)
    # Append EM result if available
    if em_list is not None:
        em_list.append(em)
    # Append EM execution time if available
    if emTime_list is not None:
        emTime_list.append(emTime)
    # Append imputation execution time if available
    if imputed_time_list is not None:
        imputed_time_list.append(imputedTime)
    
    return states_list, missing_list, time_list, KL_list, \
       inaccuracy_list, agents_list, obs_list, popularity_list, \
       imputed_list, em_list, emTime_list, imputed_time_list

def process_popularity(states, N, T, pct_range, imputation=False, optimization=False, em_iterations=None, tol=None):
    """
    Runs popularity scenario simulations and appends results.

    The function generates Markov chains, introduces popularity bias, 
    calculates RMSE, and appends results to shared lists after each run.

    Args:
        states (int): Number of states.
        N (int): Number of agents.
        T (int): Number of time steps.
        pct_range (tuple): Range of missing data percentage.
        imputation (bool): Whether to perform imputation (optional).
        optimization (bool): Whether to perform optimization (optional).
        em_iterations (int): Number of EM iterations (optional).
        tol (float): Tolerance for optimization (optional).

    Returns:
        tuple: Tuple of updated shared lists.
    """
    # Initialize shared lists to store results
    states_list = []
    missing_list = []
    emTime_list = []
    KL_list = []
    inaccuracy_list = []
    popularity_list = []
    agents_list = []
    obs_list = []
    imputed_list = []
    em_list = []
    time_list = []
    imputed_time_list = []
    
    # Generate observed transition matrix
    observed = generate_standard_transition_matrix(states)
    # Generate random prevalence ratios
    prevalence_ratios = generate_random_prevalence_ratios(states, 2)
    # Construct weighted transition matrix
    weighted_transition_matrix = construct_weighted_transition_matrix(observed, prevalence_ratios)
    # Generate initial state distribution using prevalence ratios
    initial_distribution = generate_custom_initial_distribution(states, prevalence_ratios)
    # Generate initial states for multiple agents
    initial_states = generate_initial_states(weighted_transition_matrix, N, initial_distribution)
    # Generate Markov chains for multiple agents
    markov_chain = generate_markov_chains(weighted_transition_matrix, initial_states, T, N)

    # Calculate state probabilities
    probs = np.array([np.sum(markov_chain.values == state) / markov_chain.values.size for state in range(states)])
    state_probabilities = pd.DataFrame({'State': np.arange(0, states), 'Probability': probs})
    
    # Iterate over different popularity orders and missing data percentages
    for popularity, pct in list(itertools.product([True, False], np.linspace(pct_range[0], pct_range[1]))):
            # Introduce popularity bias to the Markov chain
            result = pd.DataFrame(introduce_popularity_bias(markov_chain, state_probabilities, pct, N, T, popularity))
            start = time.time()  # Start time of execution
            estimated = extract_transition_matrix(result, states)  # Estimate transition matrix
            end = time.time()  # End time of execution
            
            # Perform imputation if requested
            final = forward_algorithm(result, estimated, T, states) if imputation else None
            estimated_imputed = extract_transition_matrix(final, states) if imputation else None
            end_impute = time.time() if imputation else None
            
            # Perform optimization if requested
            estimated_em = em_algorithm(result, N, T, states, em_iterations, tol) if optimization else None
            end_em = time.time() if optimization else None
            
            # Append results to shared lists using popAppend function
            states_list, missing_list, emTime_list, KL_list, inaccuracy_list, agents_list, obs_list, popularity_list, imputed_list, \
                em_list, time_list, imputed_time_list = popAppend(
                    states_list, states, missing_list, pct, time_list, end - start, KL_list,
                    kl_divergence(estimated, observed, states), inaccuracy_list,
                    np.linalg.norm(estimated - observed)/(np.sqrt(2*states)*np.linalg.norm(observed)), agents_list, N, obs_list, T, 
                    popularity_list, popularity, imputed_list if imputation else None,
                    np.linalg.norm(estimated_imputed - observed)/(np.sqrt(2*states)*np.linalg.norm(observed)) if imputation else None,
                    em_list if optimization else None,
                    np.linalg.norm(estimated_em - observed)/(np.sqrt(2*states)*np.linalg.norm(observed)) if optimization else None,
                    emTime_list, end_em - start if optimization else None, imputed_time_list, end_impute - start if imputation else None)
    
    # Return tuple of updated shared lists
    return states_list, missing_list, emTime_list, KL_list, inaccuracy_list, agents_list, obs_list, popularity_list, \
           imputed_list, em_list, time_list, imputed_time_list