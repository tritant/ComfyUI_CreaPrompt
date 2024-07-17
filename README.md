# ComfyUI_CreaPrompt
Generate prompts randomly

For best results, use CreaPrompt_Ultimate checkpoint

https://civitai.com/models/383364?modelVersionId=602452

It also has an extension for A1111, you can find it at

https://github.com/tritant/sd-webui-creaprompt

You can add your category easily. Just add a .csv file in the csv folder. The script will automatically add it to the interface. Each entry must be on a different line in the .csv file. The file name must have a specific format, e.g. x_xnameoffile.csv. The x are numbers which will determine the display order in the prompt (alphabetical order).
There is also a collection of 750 prompts updated regularly

![Capture d'écran 2024-07-07 124640](https://github.com/tritant/ComfyUI_CreaPrompt/assets/15909062/7ba41044-70d4-44c4-93b2-7009eaf3cf0e)

# Multi Nodes

With multi nodes, you can use up to 4 nodes at the same time, with a different category configuration for each node.

To configure the nodes, simply add/delete the categories (.csv files) in the corresponding folders (csv1, csv2, csv3).

Do not delete the collection.txt file, otherwise you will get an error.

The WF examples are in the WF folder of the custom node.

![Capture d'écran 2024-07-12 153624](https://github.com/user-attachments/assets/b62426a0-c512-4cec-9eee-ae6e311c9960)

# Weight Node

Configure it in csv+weight folder

![Capture d'écran 2024-07-17 083300](https://github.com/user-attachments/assets/96659a20-7424-492e-9ed8-cfab37c73eb1)




