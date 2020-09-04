#! /bin/bash 

rm *.json

declare -a carray
array=(navy blue)

lineCount=0;
for i in `ls *.xml`
do
echo ${i};
fileName=$(grep "^${i}" a | cut -d '|' -f2)
fileName2="${fileName}.JPG___objects.json";
echo "[" >> "${fileName2}";
while read -r string1
do 
	string2=$(echo "${string1}" | sed -e 's/<name>/#/g' | sed -e 's/<\/name>/*/g' | sed -e 's/<bndbox>/*/g' | sed -e 's/xmin/*/g' | sed -e 's/ymin/*/g' |sed -e 's/xmax/*/g' |sed -e 's/ymax/*/g' | sed -e 's/\///g' | sed -e 's/<//g' | sed -e 's/>//g' );
	#echo "string 2 is: ${string2}" >> error.log;

	IFS="#" read -ra FullLinesArray <<< "${string2}"; 
	mLen=${#FullLinesArray[@]}
        labelLine=$(echo "${FullLinesArray[0]}");
        echo " labelLine: $labelLine}" >> error.log;
        for (( i=1; i<${mLen}; i++ ));
	do
                line=$(echo "${FullLinesArray[$i]}");
		IFS="*" read -ra coordADDR <<< "${line}";
                product=$(echo "${coordADDR[0]}");
                xmin=$(echo "${coordADDR[3]}");
                ymin=$(echo "${coordADDR[5]}");
                xmax=$(echo "${coordADDR[7]}");
                ymax=$(echo "${coordADDR[9]}");
		if [ $i -eq 1 ]
		then
        		echo "    {" >> "${fileName2}";
		else
        		echo "    ,{" >> "${fileName2}";
		fi 
		echo "\"type\":\"bbox\",\"classId\":12698,\"probability\":100,\"points\":{\"x1\":${xmin},\"x2\":${xmax},\"y1\":${ymin},\"y2\":${ymax}},\"groupId\":0,\"pointLabels\":{},\"locked\":false,\"visible\":true,\"attributes\":[],\"className\":\"${product}\"}" >> "${fileName2}";

	done
done < ${i}
echo "]" >> "${fileName2}";
done
exit 0

