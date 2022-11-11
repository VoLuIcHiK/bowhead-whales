from icrawler.builtin import GoogleImageCrawler

req = "bowhead whale aerial photography"
num = int(input("Введите число фотографий:"))
dir = str(input("Введите имя папки:"))
web = GoogleImageCrawler(storage={"root_dir":f"D:\{dir}"})
web.crawl(keyword=req,max_num=num)