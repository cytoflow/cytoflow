import FlowCytometryTools
import sklearn.mixture as mix
import numpy as np
import scipy as sp
from pandas import *
from scipy.stats import *
from synbio_flow import Experiment

class Operation:
    
    '''An Operation represents a function to be performed on an experiment.
    An operation is run by calling the run_operation method.
    The data and history of the input experiment should remain the same after
    an operation is performed. Any outputs (experiments, numerical data, etc) will
    be returned by the run_operation method.
    '''
    
    def __init__(self):
        self.parameters = {}
    
    # if the return type is new FCS data, return a new Experiment, with same
    # settings but new data. Will never mutate the previous experiment.
    def run_operation(self, experiment):
        raise NotImplementedError
    
    def get_parameters_needed(self):
        return self.parameters.keys()
        
    def set_parameter(self, param_name, param_value):
        if not param_name in self.parameters.keys():
            raise ValueError('parameter not appropriate for operation')
        else:
            self.parameters[param_name] = param_value
        
class Transform(Operation):
    
    '''Returns a new experiment with the specified transformation applied to the
    original data. Currently supported transformations are base_10 hyperlog ('hlog'),
    base_10 truncated log ('tlog') and linear scaling. If no channels are specified
    the transformation is applied to all channels.
    '''
    
    def __init__(self, trans_type):
        Operation.__init__(self)
        self.trans_type = trans_type
        self.parameters['direction'] = 'forward'
        self.parameters['channels'] = None
    
    def run_operation(self, experiment):
        channel_corr_names = experiment.find_orig_channels(self.parameters['channels'])
        new_populations = []
        for fcs in experiment.get_populations():
            new_populations.append(fcs.new_updated_pop(fcs.get_file().transform(self.trans_type, \
            channels = channel_corr_names)))
        result = experiment.new_updated_exp(new_populations)
        result.add_op(self)
        return result
        
class Statistics(Operation):
    
    '''Returns a data table of the specified statistic applied to the experiment
    data on the specified channels. If no channels are specified, computes and
    returns the statistic for all channels. Currently supports median ('median'),
    arithmetic mean ('mean'), standard deviation ('std'), and geometric mean ('gmean').
    '''
    
    def __init__(self, stats_type):
        Operation.__init__(self)
        self.stats_type = stats_type
        self.parameters['channels'] = None
        
    def run_operation(self, experiment):
        channel_corr_names = experiment.find_orig_channels(self.parameters['channels'])
        data = DataFrame(columns = self.parameters['channels'])
        rowlabels = []
        i=0
        for fcs in experiment.get_populations():
            file_data = []
            for channel in channel_corr_names:
                if self.stats_type == 'median':
                    file_data.append(fcs.get_file().data[channel].median(axis = 1));
                elif self.stats_type == 'mean':
                    file_data.append(fcs.get_file().data[channel].mean(axis = 1));
                elif self.stats_type == 'gmean':
                    file_data.append(gmean(fcs.data[channel].values.tolist()))
                elif self.stats_type == 'std':
                    file_data.append(fcs.get_file().data[channel].std(axis = 1))
                else:
                    raise IllegalArgumentException('not a supported stats type')
            data.loc[i] = file_data
            i += 1
            rowlabels.append(fcs.get_file().get_meta_fields('$FIL')['$FIL'])
        data.set_index(np.array(rowlabels), inplace = True)
        return data

class GateAll(Operation):
    
    '''Applies the given gate to all of the samples in the experiment. An experiment
    can only have one gate of a given name.
    '''
    
    def __init__(self, gate, gate_name):
        Operation.__init__(self)
        self.gate = gate
        self.gate_name = gate_name
    
    def run_operation(self, experiment):
        new_populations = []
        for population in experiment.get_populations():
            new_pop=population.new_updated_pop(population.get_file().gate(self.gate))
            new_pop.add_gate(self)
            new_populations.append(new_pop)
        return experiment.new_updated_exp(new_populations)
        
    def __repr__(self):
        return self.gate_name
        
class ChangeOneGate(Operation):
    
    '''Changes a previously-applied gate in one of the samples. The experiment must
    contain a population with the given fcs_id and must have a gate with the same
    name applied to all of the samples.
    '''
    
    def __init__(self, gate, gate_name, fcs_id):
        Operation.__init__(self)
        self.gate = gate
        self.gate_name = gate_name
        self.fcs_id = fcs_id
        
    def run_operation(self, experiment):
        population = experiment.population_map[self.fcs_id]
        count = 0
        for gated in population.get_gates():
            if self.gate_name == gated.gate_name:
                index = count
            count +=1
        population.gate_list.pop(index)
        population.gate_list.insert(index, self.gate)
        new_file = population.original
        for to_gate in population.get_gates():
            new_file = new_file.gate(to_gate)
        new_pop = population.new_updated_pop(new_file)
        new_file_list = [new_pop]
        for population in experiment.get_populations():
            if population.ID != self.fcs_id:
                new_file_list.append(population)
        return experiment.new_updated_exp(new_file_list)
        
    def __repr__(self):
        return self.gate_name + " on " + self.fcs_id
        
class OneDimMix(Operation):
    
    '''Fits data to a 1D Gaussian mixture model using EM. Returns num_exp <= num_comp new 
    experiments, each containing data from one component of the 1D mixture model.
    If the data cannot be adequately fit using the specified number of components, 
    returns a warning. Attempts to fit all data to num_comp populations, but may
    fit some populations to less than num_comp components.
    '''
    
    def __init__(self, channel, num_comp = 2):
        Operation.__init__(self)
        self.channel = channel
        self.parameters['num_comp'] = num_comp
        
    def run_operation(self, experiment):
        pops = experiment.get_populations()
        channel = experiment.find_orig_channels([self.channel])
        wrong_comp_num = []
        alpha_list = []
        new_populations = [[] for i in xrange(self.parameters['num_comp'])]
        all_thresholds = []
        all_orders = []
        new_experiments = []
        for population in pops:
            bic_list = []
            gmm_list = []
            data = population.get_file().data[channel].values
            for num_comp in xrange(1,self.parameters['num_comp']+1):
                gmm = mix.GMM(n_components = num_comp)
                gmm.fit(data)
                print gmm.bic(data), num_comp
                bic_list.append(gmm.bic(data))
                gmm_list.append(gmm)
            best_num_comp = bic_list.index(min(bic_list))+1
            best_gmm = gmm_list[best_num_comp-1]
            if best_num_comp != self.parameters['num_comp']:
                wrong_comp_num.append([population, best_num_comp, best_gmm])
            else:
                gate_thresholds = gmm_thresholds(best_gmm, min(data)[0], max(data)[0], best_num_comp)
                sorted_order = sorted(gate_thresholds[1], key = lambda x: gate_thresholds[0][gate_thresholds[1].index(x)])
                all_orders.append(sorted_order)
                print sorted_order
                sorted_thresholds = sorted(gate_thresholds[0])
                all_thresholds.append(sorted_thresholds)
                for i in xrange(len(sorted_thresholds)-1):
                    gate = FlowCytometryTools.ThresholdGate(sorted_thresholds[i], channel, 'above')
                    gate2 = FlowCytometryTools.ThresholdGate(sorted_thresholds[i+1], channel, 'below')
                    population.get_file().plot(channel, gates=[gate2], bins=100)
                    new_populations[sorted_order[i]].append(population.new_updated_pop(population.get_file().gate(gate).gate(gate2)))
        '''avg_thresholds = np.mean(np.array(all_thresholds), axis = 0)
        for data in wrong_comp_num:
            
            for i in xrange(len(avg_thresholds)-1):
                gate = FlowCytometryTools.ThresholdGate(avg_thresholds[i], channel, 'above')
                gate2 = FlowCytometryTools.ThresholdGate(avg_thresholds[i+1], channel, 'below')
                data[0].get_file().plot(channel, gates=[gate2], bins=100)
                new_populations[comp_num[i]].append(data[0].new_updated_pop(data[0].get_file().gate(gate).gate(gate2)))
              '''      
        for pop_set in new_populations:
            new_experiments.append(experiment.new_updated_exp(pop_set))
        return new_experiments    
            
def gmm_thresholds(gmm, low_lim, upp_lim, num_comp):
    
    ''' Returns 1D gate thresholds for a GMM.
    '''
    
    tolerance = 10
    results = []
    
    curr_probs=gmm.predict_proba([low_lim])
    curr_top = np.argmax(curr_probs)
    comp_num = [curr_top]
    for i in xrange(low_lim, upp_lim, tolerance):
        curr_probs=gmm.predict_proba([[i]])
        next_top = np.argmax(curr_probs)
        if next_top != curr_top:
            curr_top = next_top
            results.append(i)
            comp_num.append(curr_top)
    results.append(upp_lim)
    results = [low_lim]+results
    print [results, comp_num]
    return [results, comp_num]