import print_queue
import timeIt


if __name__ == '__main__':
    pq = print_queue.PrintQueue()
    pq.update_joblist()
    print(f"File to send to printer: {pq.get_next_job()}")