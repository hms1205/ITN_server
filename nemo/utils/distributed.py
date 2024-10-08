# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import torch

from nemo.utils import logging

try:
    from apex.transformer import parallel_state

    HAVE_APEX = True
except (ImportError, ModuleNotFoundError):
    HAVE_APEX = False


def initialize_distributed(args, backend='gloo'):
    """Initialize torch.distributed."""
    # Get local rank in case it is provided.
    local_rank = args.local_rank

    # Get rank and world size.
    rank = int(os.getenv('RANK', '0'))
    world_size = int(os.getenv("WORLD_SIZE", '1'))

    logging.info(
        f'Initializing torch.distributed with local_rank: {local_rank}, rank: {rank}, world_size: {world_size}'
    )

    # Set the device id.
    device = rank % torch.cuda.device_count()
    if local_rank is not None:
        device = local_rank
    torch.cuda.set_device(device)

    # Call the init process.
    init_method = 'tcp://'
    master_ip = os.getenv('MASTER_ADDR', 'localhost')
    master_port = os.getenv('MASTER_PORT', '6000')
    init_method += master_ip + ':' + master_port
    torch.distributed.init_process_group(backend=backend, world_size=world_size, rank=rank, init_method=init_method)
    return local_rank, rank, world_size


def gather_objects(partial_results_list, main_rank=None):
    """
    Collect objects (e.g., results) from all GPUs.
    Useful for inference over multiple GPUs with DDP.
    
    Use main_rank to specify which rank will be used to gather results.
    This allows to continue execution on the main_rank only after the gather.

    Args:
        partial_results_list: list of partial results from each GPU
        main_rank: rank of the main process to collect results from all GPUs (useful for collecting results in a target rank)
    
    
    Example:
        predictions = gather_objects(predictions,main_rank=0)
        # all but rank 0 will return None
        if predictions is None:
            return
        
        # from here only rank 0 should contiue
        pickle.dump(predictions, open(output_fname, "wb"))
    """
    # do not fail when DDP is not initialized
    if parallel_state.is_unitialized():
        return partial_results_list

    rank = parallel_state.get_data_parallel_rank()
    world_size = parallel_state.get_data_parallel_world_size()
    # return input when no DDP is used
    if world_size == 1:
        return partial_results_list

    gathered_results = [None for _ in range(world_size)]
    torch.distributed.all_gather_object(gathered_results, partial_results_list)

    # return None to non-main ranks
    if main_rank is not None:
        if rank != main_rank:
            return None

    # return collected results
    results_list = []
    for r in gathered_results:
        results_list.extend(r)

    return results_list
