from utils import *
import json

if __name__ == '__main__':

    data_path = 'your_data_path'

    datas = prepare_dataset(data_path)
    """
    datas = [['王大亮是否开了病理学这门课？', '[T_王大亮]是否开了[C_course-v1:TsinghuaX+20190222+2019_T1]这门课？', '老师_课程', '是', 'None', 'B'],[...]]
    """
    count = 0
    for data in datas:
        llm_call = 1
        print('data:', data)
        question = data[0]
        try:
            entity_chains = extract_entity_chain(data[0])
        except:
            continue
        print('clues:', entity_chains)
        invovled_info = []
        all_routes = []
        possible_routes = [] # not currently in use, but may be employed in the future to further enhance the effectiveness
        for entity in entity_chains:
            nodes = query_node(entity)
            if nodes:
                for node in nodes:
                    all_routes.append([node])
                    if node[0] in entity_chains:
                        invovled_info.append([node[0], entity])
                    else:
                        invovled_info.append([entity])
                    break

        """
        The loop will terminate under two conditions: 
        first, when the target path is found; 
        second, when no paths are found to the next node.
        """
        while 1:   
            end_flag = 0
            new_routes = []
            new_info = []
            temp_all_routes = []
            temp_invovled_info = []
            for i in range(len(all_routes)):      
               try:    
                current_route = all_routes[i] 

                current_info = invovled_info[i] # clues that have been used by the current route
                related_nodes = get_related_nodes_by_id(current_route[-1][2]) # (label, name, id, relation)
               
                if len(current_route) > 1:
                    related_nodes = [node for node in related_nodes if node[2] != current_route[-2][2]]
                candidates = [] 
                current_flag = 0
                prior = 0
                for related_node in related_nodes:
                    # character matching
                    if related_node[1] in entity_chains and related_node[1] not in current_info:
                        new_routes.append(current_route+[related_node])
                        tmp_info = current_info+[related_node[1]]
                        current_flag = 1

                        if related_node[0] in entity_chains and related_node[0] not in current_info:
                            tmp_info.append(related_node[0])
                        new_info.append(tmp_info)


                label_set = set()

                # fuzzy matching
                if current_flag == 0:
                    extracted_nodes = [(r, label) for label, _, _, r in related_nodes]
                    pruned_nodes = prune_node(question, list(set(entity_chains)-set(current_info)), (current_route[-1][0], current_route[-1][1]), list(set(extracted_nodes)))
                    llm_call += 1
                    for related_node in related_nodes:
                        if (related_node[3], related_node[0]) in [(e[0], e[1]) for e in pruned_nodes]:
                            candidates.append(related_node)
                            label_set.add(related_node[0])

                # rough matching and exact matching

                if candidates != []:
                    for label in label_set:
                        temp = []
                        temp1 = []
                        selected_nodes = []
                        for candidate in candidates:
                            if candidate[0] == label:
                                temp.append((candidate[0], candidate[1]))
                                temp1.append(candidate)
                        temp = list(set(temp))
                        
                        if len(temp) > 10:
                            continue
                        if set(entity_chains)-set(current_info+[label]) != set(): 
                            selected_nodes = select_node(question, list(set(entity_chains)-set(current_info+[label])), temp)
                            llm_call += 1
                            for node in selected_nodes:
                                for n in temp1:
                                    if n[0] == node[0] and n[1] == node[1]:                              
                                        this_info = info_match(question, list(set(entity_chains)-set(current_info+[label])), (node[0], node[1]))
                                        llm_call += 1
                                        if this_info == []:
                                            # no info matched
                                            possible_routes.append(current_route+current_info)
                                        elif label in entity_chains:
                                            new_routes.append(current_route+[n])
                                            new_info.append(current_info+[this_info, label])
                                        else:
                                            new_routes.append(current_route+[n])
                                            new_info.append(current_info+[this_info])
                        else:
                            for node in temp1:
                                new_routes.append(current_route+[node])
                                new_info.append(current_info+[label])

                        

               except:
                   continue 
            if new_routes != []: # if new routes are found, update the current routes and clues
                all_routes = []
                for i in range(len(new_info)):
                    if set(new_info[i]) == set(entity_chains):  # if the target path is found, terminate the loop
                        end_flag = 1
                        all_routes.append(new_routes[i])
                if end_flag == 0:
                    all_routes = new_routes
                    invovled_info = new_info
            else: # if no new routes are found, terminate the loop
                print('unused clues')
                break

            if end_flag == 1:
                break
        info_2_llm = []
        for route in all_routes:
            if len(route) == 1:
                info_2_llm.append((route[0][1], '无', '无')) #无 is None in Chinese
            else:
                info_2_llm.extend([(route[i][1], route[i+1][3], route[i+1][1]) for i in range(len(route)-1)])

        info_2_llm = list(set(info_2_llm))
        print(info_2_llm)

        try:
            answer = answer_question(question, info_2_llm)
        except Exception as e:
            answer = e

        result = {
            'data': data,
            'answer': answer,
            'llm_call': llm_call
        }

        with open('your_result_path', 'a', encoding='utf-8') as file:
            json.dump(result, file, ensure_ascii=False)
            file.write('\n')
            file.write(str(info_2_llm))
            file.write('\n')
        count+=1
        print(count, 'done')
