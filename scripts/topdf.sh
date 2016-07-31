# Lower Case and numericals
echo converting files starting with lower case and numerical characters
wkhtmltopdf -L 25 -R 25 -T 20 -B 20  [0-9]*.html [[:lower:]]*.html volume1.pdf

# Upper Case
for x in {A..Z}
do
	echo `ls -al $x*.html | wc -l` files starting with $x
	wkhtmltopdf -L 25 -R 25 -T 20 -B 20  $x*.html $x.pdf
done
